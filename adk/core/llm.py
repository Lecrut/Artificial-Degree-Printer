from __future__ import annotations

import json
import time
import urllib.error
from pathlib import Path
from typing import Any, Callable

from adk.core.connection import LLMConnectionManager
from adk.core.logger import get_process_logger
from adk.core.models import resolve_adk_path

_CUSTOM_LLM_HANDLER: Callable[[str, dict[str, Any], str], dict[str, Any]] | None = None


def set_llm_handler(handler: Callable[[str, dict[str, Any], str], dict[str, Any]] | None) -> None:
    """Register or clear a custom LLM callback for testing or custom runtime routing."""
    global _CUSTOM_LLM_HANDLER
    _CUSTOM_LLM_HANDLER = handler


def _extract_json_from_text(text: str) -> dict[str, Any] | list[Any] | None:
    """Attempt to extract a JSON object or list from raw model output."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3:
            stripped = "\n".join(lines[1:-1]).strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return None


def _default_simulated_response(agent_name: str, system_prompt: str, payload: dict[str, Any], tier: str) -> dict[str, Any]:
    """Deterministic fallback response structured by agent role when running in offline/mock mode."""
    if "task_planner" in agent_name or "initial_task_planner" in agent_name:
        prompt_text = str(payload.get("user_prompt", "Build module"))
        target_node = str(payload.get("target_node", "v1"))
        include_docs = bool(payload.get("include_docs", True))
        if payload.get("tasks"):
            tasks = payload["tasks"]
        else:
            tasks = [
                {
                    "task_id": "T1",
                    "description": f"Implement configuration parameters for: {prompt_text}",
                    "target_node": target_node,
                    "assigned_agent": "seed_coder",
                    "status": "TODO",
                },
                {
                    "task_id": "T2",
                    "description": f"Implement core logic and unit tests for: {prompt_text}",
                    "target_node": "v2",
                    "assigned_agent": "seed_tester",
                    "status": "TODO",
                },
            ]
            if include_docs:
                tasks.append(
                    {
                        "task_id": "T3",
                        "description": f"Document symbolic results for: {prompt_text}",
                        "target_node": "v4",
                        "assigned_agent": "seed_writer",
                        "status": "TODO",
                    }
                )
        return {
            "tasks": tasks,
            "missing_agent_specialization": payload.get("missing_agent_specialization"),
        }

    if "remediation_planner" in agent_name:
        err_rep = payload.get("error_report") or {}
        failed_id = err_rep.get("failed_task_id", "T1")
        failed_node = err_rep.get("failed_node", "v1")
        failed_agent = err_rep.get("failed_agent", "seed_coder")
        return {
            "root_cause_diagnosis": f"Failure identified in {failed_node} by supervisor.",
            "remediation_strategy": "Surgically patch AST or benchmark without altering completed thesis sections.",
            "surgical_tasks": [
                {
                    "task_id": f"{failed_id}_FIX",
                    "description": f"Surgically patch issues in {failed_node}",
                    "target_node": failed_node,
                    "assigned_agent": failed_agent,
                    "status": "TODO",
                }
            ],
        }

    if "sota_researcher" in agent_name:
        return {
            "bibtex_entries": "@article{vaswani2017attention,\n  author = {Vaswani, Ashish and others},\n  title = {Attention Is All You Need},\n  journal = {NeurIPS},\n  year = {2017}\n}\n",
            "literature_review_section": "\\subsection{Analiza Stanu Wiedzy}\nW literaturze przedmiotu podstawowe znaczenie ma praca \\cite{vaswani2017attention}...",
            "citation_keys": ["vaswani2017attention"],
            "summary": "Synthesized SOTA review with formal BibTeX bibliography.",
        }

    if "task_critic_guard" in agent_name:
        tasks = payload.get("tasks", [])
        registry = payload.get("agent_registry", {}).get("agents", {})
        blast_nodes = set(payload.get("blast_radius_nodes", []))
        issues: list[str] = []
        if not tasks:
            issues.append("Task queue is empty.")
        covered_nodes = {t.get("target_node") for t in tasks}
        for b_node in blast_nodes:
            if b_node not in covered_nodes:
                issues.append(f"Blast radius node '{b_node}' is not covered by any planned task.")
        for task in tasks:
            agent_id = task.get("assigned_agent")
            if registry and (agent_id not in registry or not registry[agent_id].get("active", True)):
                issues.append(f"Assigned agent '{agent_id}' is missing or inactive in agent_registry.json.")
        return {
            "status": "FAIL" if issues else "PASS",
            "approved": len(issues) == 0,
            "issues": issues,
        }

    if "redteam_critic_guard" in agent_name or "code_auditor" in agent_name or "symbolic_auditor" in agent_name:
        force_fail = bool(payload.get("force_fail", False))
        issues = list(payload.get("issues", []))
        status = "FAIL" if (force_fail or issues) else "PASS"
        return {
            "status": status,
            "issues": issues if issues else (["Detected cross-artifact inconsistency"] if force_fail else []),
        }

    if "evolution_architect" in agent_name:
        if payload.get("contradictory_requirements"):
            return {
                "decision": "HITL",
                "question": "Wykryto sprzeczne wymagania projektowe. Proszę o doprecyzowanie priorytetu.",
            }
        if payload.get("missing_specialization"):
            return {
                "decision": "CREATE_AGENT",
                "specialization": payload["missing_specialization"],
                "layer": payload.get("target_layer", "building"),
            }
        if payload.get("split_agent_id"):
            return {
                "decision": "SPLIT_AGENT",
                "agent_id": payload["split_agent_id"],
                "sub_specializations": payload.get("sub_specializations", ["unit_testing", "edge_case_testing"]),
            }
        if payload.get("synthesize_tool"):
            return {
                "decision": "CREATE_TOOL",
                "tool_name": payload.get("tool_name", "custom_validator.py"),
                "tool_code": payload.get("tool_code", ""),
            }
        return {
            "decision": "MUTATE_AGENT",
            "agent_id": payload.get("failed_agent", "seed_coder"),
            "rule": payload.get("suggested_rule", "Zawsze weryfikuj spójność typów i eksportowanych nazw AST."),
        }

    return {
        "action": "executed",
        "agent": agent_name,
        "model_tier": tier,
        "summary": f"Processed payload with {len(system_prompt)} chars of instructions.",
    }


def call_agent(
    md_path: str | Path,
    user_payload: dict[str, Any],
    model_tier: str = "SML",
    provider: str | None = None,
) -> dict[str, Any]:
    """Load declarative agent instructions from a .md file, call LLM (Google/Ollama/Mock), log full exchange, and return output."""
    path = resolve_adk_path(md_path)
    if not path.exists():
        raise FileNotFoundError(f"Declarative agent file not found: {md_path}")

    if model_tier not in ("SML", "LRM"):
        raise ValueError(f"Unsupported model_tier '{model_tier}'. Expected 'SML' or 'LRM'.")

    system_prompt = path.read_text(encoding="utf-8")
    serialized_payload = json.dumps(user_payload, ensure_ascii=False, indent=2)
    combined_prompt = (
        f"{system_prompt.strip()}\n\n"
        f"=== INPUT JSON PAYLOAD ===\n"
        f"{serialized_payload}\n"
    )

    conn = LLMConnectionManager(provider=provider)
    active_provider = conn.resolve_provider()
    model_name = conn.resolve_model_name(active_provider, model_tier)
    logger = get_process_logger()

    start_t = time.perf_counter()

    if _CUSTOM_LLM_HANDLER is not None:
        custom_out = _CUSTOM_LLM_HANDLER(system_prompt, user_payload, model_tier)
        elapsed_ms = (time.perf_counter() - start_t) * 1000.0
        raw_str = json.dumps(custom_out, ensure_ascii=False, indent=2)
        logger.log_agent_exchange(
            agent_md=str(path),
            provider="custom_handler",
            model_tier=model_tier,
            model_name=model_name,
            system_prompt=system_prompt,
            user_payload=user_payload,
            combined_prompt=combined_prompt,
            raw_response=raw_str,
            parsed_output=custom_out,
            elapsed_ms=elapsed_ms,
        )
        return {
            "status": "ok",
            "provider": "custom_handler",
            "agent_md": str(path),
            "model_tier": model_tier,
            "model_name": model_name,
            "prompt_sent": combined_prompt,
            "output": custom_out,
        }

    if active_provider in ("google", "ollama"):
        try:
            if active_provider == "google":
                api_res = conn.call_google_gemini(model_name, combined_prompt)
            else:
                api_res = conn.call_ollama(model_name, combined_prompt)

            raw_text = api_res.get("raw_text", "{}")
            parsed = _extract_json_from_text(raw_text)
            if not isinstance(parsed, dict):
                fallback = _default_simulated_response(path.stem, system_prompt, user_payload, model_tier)
                fallback["llm_raw_text"] = raw_text
                parsed = fallback

            elapsed_ms = (time.perf_counter() - start_t) * 1000.0
            logger.log_agent_exchange(
                agent_md=str(path),
                provider=active_provider,
                model_tier=model_tier,
                model_name=model_name,
                system_prompt=system_prompt,
                user_payload=user_payload,
                combined_prompt=combined_prompt,
                raw_response=raw_text,
                parsed_output=parsed,
                elapsed_ms=elapsed_ms,
            )
            return {
                "status": "ok",
                "provider": active_provider,
                "agent_md": str(path),
                "model_tier": model_tier,
                "model_name": model_name,
                "prompt_sent": combined_prompt,
                "output": parsed,
            }
        except (urllib.error.URLError, TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
            logger.log_step(
                "CONNECTION_FALLBACK",
                f"Nie udało się połączyć z '{active_provider}' ({model_name}): {exc}. Przełączam na deterministyczny fallback.",
            )

    simulated = _default_simulated_response(path.stem, system_prompt, user_payload, model_tier)
    elapsed_ms = (time.perf_counter() - start_t) * 1000.0
    raw_sim = json.dumps(simulated, ensure_ascii=False, indent=2)
    logger.log_agent_exchange(
        agent_md=str(path),
        provider="mock",
        model_tier=model_tier,
        model_name=model_name,
        system_prompt=system_prompt,
        user_payload=user_payload,
        combined_prompt=combined_prompt,
        raw_response=raw_sim,
        parsed_output=simulated,
        elapsed_ms=elapsed_ms,
    )
    return {
        "status": "ok",
        "provider": "mock",
        "agent_md": str(path),
        "model_tier": model_tier,
        "model_name": model_name,
        "prompt_sent": combined_prompt,
        "output": simulated,
    }

