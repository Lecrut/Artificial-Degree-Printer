from __future__ import annotations

import json
import os
import re
import time
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from adk.core.connection import LLMConnectionManager
from adk.core.logger import get_process_logger
from adk.core.models import resolve_adk_path

_CUSTOM_LLM_HANDLER: Callable[[str, dict[str, Any], str], dict[str, Any]] | None = None
_LLM_TELEMETRY: dict[str, Any] = {
    "calls_count": 0,
    "live_network_calls": 0,
    "total_inference_ms": 0.0,
    "models_used": [],
    "call_log": [],
    "interactions": [],
}


def reset_llm_telemetry() -> None:
    """Reset per-task LLM call counters, timing metrics, and full interaction records."""
    _LLM_TELEMETRY["calls_count"] = 0
    _LLM_TELEMETRY["live_network_calls"] = 0
    _LLM_TELEMETRY["total_inference_ms"] = 0.0
    _LLM_TELEMETRY["models_used"] = []
    _LLM_TELEMETRY["call_log"] = []
    _LLM_TELEMETRY["interactions"] = []


def get_llm_telemetry() -> dict[str, Any]:
    """Return a snapshot of LLM call counts, network inference time, models used, and full interactions."""
    return {
        "calls_count": int(_LLM_TELEMETRY["calls_count"]),
        "live_network_calls": int(_LLM_TELEMETRY["live_network_calls"]),
        "total_inference_ms": round(float(_LLM_TELEMETRY["total_inference_ms"]), 2),
        "models_used": list(_LLM_TELEMETRY["models_used"]),
        "call_log": list(_LLM_TELEMETRY["call_log"]),
        "interactions": list(_LLM_TELEMETRY.get("interactions", [])),
    }


def set_llm_handler(handler: Callable[[str, dict[str, Any], str], dict[str, Any]] | None) -> None:
    """Register or clear a custom LLM callback for testing or custom runtime routing."""
    global _CUSTOM_LLM_HANDLER
    _CUSTOM_LLM_HANDLER = handler


def _extract_json_from_text(text: str) -> dict[str, Any] | list[Any] | None:
    """Robustly extract a JSON object or list from raw model output (handling <think> blocks, markdown fences, and prose)."""
    if not text or not text.strip():
        return None

    # 1. Strip reasoning blocks (<think>...</think>) emitted by reasoning models
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()

    # 2. Direct parse attempt
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 3. Extract from ```json ... ``` or ``` ... ``` fenced blocks anywhere in the response
    fence_match = re.search(r"```(?:json)?\s*\n(.*?)```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if fence_match:
        fenced_body = fence_match.group(1).strip()
        try:
            return json.loads(fenced_body)
        except json.JSONDecodeError:
            pass

    # 4. Scan for the first valid JSON object '{...}' or array '[...]' using raw_decode
    decoder = json.JSONDecoder()
    for idx, ch in enumerate(cleaned):
        if ch in ("{", "["):
            try:
                obj, _ = decoder.raw_decode(cleaned[idx:])
                if isinstance(obj, (dict, list)):
                    # If model wrapped everything inside a single 'response' field, unwrap it if possible
                    if isinstance(obj, dict) and "response" in obj and len(obj) == 1:
                        inner = obj["response"]
                        if isinstance(inner, dict):
                            return inner
                        if isinstance(inner, str) and ("{" in inner or "[" in inner):
                            try:
                                sub = json.loads(inner)
                                if isinstance(sub, (dict, list)):
                                    return sub
                            except Exception:
                                pass
                    return obj
            except json.JSONDecodeError:
                continue

    return None


def _default_simulated_response(agent_name: str, system_prompt: str, payload: dict[str, Any], tier: str) -> dict[str, Any]:
    """Deterministic fallback response structured by agent role when running in offline/mock mode."""
    from adk.benchmarks.tictactoe import (
        TICTACTOE_CONFIG_AST_NODES,
        TICTACTOE_CORE_CODE,
        TICTACTOE_DOC_SECTION_CONTENT,
        TICTACTOE_DOC_SECTION_TITLE,
        TICTACTOE_INITIAL_CSV,
        TICTACTOE_TEST_CODE,
    )
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
            "thesis_type": "engineering",
            "hitl_gate": "GATE_1_OUTLINE_APPROVAL",
            "academic_blueprint": {
                "thesis_title": f"Design and Empirical Evaluation: {prompt_text[:60]}",
                "thesis_statement": "Deterministic neuro-symbolic verification eliminates metric hallucinations.",
                "baseline_comparison": "Comparison of the proposed algorithm against a random baseline policy.",
                "planned_visualizations": [
                    "System architecture diagram in TikZ/Mermaid",
                    "Comparative win-rate and convergence plots in matplotlib",
                ],
            },
            "tasks": tasks,
            "missing_agent_specialization": payload.get("missing_agent_specialization"),
        }

    if "seed_coder" in agent_name:
        target_file = str(payload.get("target_file", "config.py"))
        if "config" in target_file:
            return {
                "ast_edits": [{"symbol": sym, "code": code} for sym, code in TICTACTOE_CONFIG_AST_NODES],
                "summary": "Defined strictly typed learning hyperparameters in config.py.",
            }
        return {
            "source_code": TICTACTOE_CORE_CODE,
            "ast_edits": [],
            "summary": "Implemented core algorithm and baseline evaluation logic in core.py.",
        }

    if "seed_tester" in agent_name:
        return {
            "source_code": TICTACTOE_CORE_CODE,
            "test_file": "test_core.py",
            "test_code": TICTACTOE_TEST_CODE,
            "benchmark_file": "results.csv",
            "csv_content": TICTACTOE_INITIAL_CSV,
            "plot_script": "",
            "summary": "Executed pytest unit tests and comparative benchmarks (baseline vs. proposed) saved to results.csv.",
        }

    if "seed_writer" in agent_name:
        return {
            "section_title": TICTACTOE_DOC_SECTION_TITLE,
            "section_content": TICTACTOE_DOC_SECTION_CONTENT,
            "summary": "Authored thesis subsection using symbolic pointers \\ref_ast and \\ref_csv.",
        }


    if "remediation_planner" in agent_name:
        err_rep = payload.get("error_report") or {}
        failed_id = err_rep.get("failed_task_id", "T1")
        failed_node = err_rep.get("failed_node", "v1")
        failed_agent = err_rep.get("failed_agent", "seed_coder")
        registry = payload.get("agent_registry", {}).get("agents", {})
        if failed_agent in registry and not registry[failed_agent].get("active", True):
            for cand_id, cand_meta in registry.items():
                if cand_meta.get("parent_agent") == failed_agent and cand_meta.get("active", True):
                    failed_agent = cand_id
                    break
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
            "updated_pending_tasks": payload.get("updated_pending_tasks", []),
        }


    if "sota_researcher" in agent_name:
        return {
            "bibtex_entries": "@article{vaswani2017attention,\n  author = {Vaswani, Ashish and others},\n  title = {Attention Is All You Need},\n  journal = {NeurIPS},\n  year = {2017}\n}\n",
            "literature_review_section": "\\subsection{State-of-the-Art Literature Review}\nFoundational work in sequence modeling includes \\cite{vaswani2017attention}...",
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

    if "prompt_consolidator" in agent_name:
        acc_rules = payload.get("accumulated_rules", [])
        joined_summary = " | ".join(str(r).strip() for r in acc_rules[:4])
        return {
            "agent_id": payload.get("agent_id", "seed_coder"),
            "consolidated_invariant": (
                f"Consolidated directive from {len(acc_rules)} rules: {joined_summary}"
            ),
            "redacted_base_prompt": None,
            "discarded_redundant_rules_count": max(0, len(acc_rules) - 1),
            "summary": f"Redacted and consolidated {len(acc_rules)} prompt rules.",
        }


    if "evolution_architect" in agent_name:
        if payload.get("contradictory_requirements"):
            return {
                "action": "HITL",
                "decision": "HITL",
                "question": "Wykryto sprzeczne wymagania projektowe. Proszę o doprecyzowanie priorytetu.",
            }
        if payload.get("missing_specialization"):
            return {
                "action": "CREATE_AGENT",
                "decision": "CREATE_AGENT",
                "specialization": payload["missing_specialization"],
                "layer": payload.get("target_layer", "building"),
                "domain": payload.get("target_layer", "building"),
            }
        if payload.get("split_agent_id") or int(payload.get("agent_failure_count", 0)) >= 2:
            target_split = payload.get("split_agent_id") or payload.get("failed_agent", "seed_tester")
            return {
                "action": "SPLIT_AGENT",
                "decision": "SPLIT_AGENT",
                "agent_id": target_split,
                "sub_specializations": payload.get("sub_specializations", ["unit_testing", "edge_case_testing"]),
            }
        if payload.get("synthesize_tool") or payload.get("validator_code") or payload.get("tool_code"):
            v_name = payload.get("validator_name") or payload.get("tool_name") or "custom_validator.py"
            v_code = payload.get("validator_code") or payload.get("tool_code") or ""
            bad_s = payload.get("bad_sample_input") or payload.get("bad_sample") or "BAD"
            good_s = payload.get("good_sample_input") or payload.get("good_sample") or "GOOD"
            return {
                "action": "CREATE_TOOL",
                "decision": "CREATE_TOOL",
                "validator_name": v_name,
                "validator_code": v_code,
                "bad_sample_input": bad_s,
                "good_sample_input": good_s,
                "tool_name": v_name,
                "tool_code": v_code,
                "bad_sample": bad_s,
                "good_sample": good_s,
            }
        return {
            "action": "MUTATE_AGENT",
            "decision": "MUTATE_AGENT",
            "agent_id": payload.get("failed_agent", "seed_coder"),
            "rule": payload.get("suggested_rule", "Always verify type consistency and exported AST symbol names."),
        }



    return {
        "action": "executed",
        "agent": agent_name,
        "model_tier": tier,
        "summary": f"Processed payload with {len(system_prompt)} chars of instructions.",
    }


def summarize_agent_decision(agent_name: str, payload: dict[str, Any], output: dict[str, Any]) -> str:
    """Generate a concise, human-readable Polish summary of the decision made by the agent/LLM."""
    if not isinstance(output, dict):
        return f"Wynik: {str(output)[:100]}"

    name = agent_name.lower()

    # 1. Planning agents
    if "planner" in name:
        if "remediation" in name:
            tasks = output.get("surgical_tasks") or output.get("tasks") or []
            diag = output.get("root_cause_diagnosis") or output.get("remediation_strategy") or output.get("summary") or ""
            if not diag:
                diag = output.get("reason") or (output.get("context", {}).get("suggested_rule", "") if isinstance(output.get("context"), dict) else "")
            if not diag and "action" in output:
                diag = f"Akcja naprawcza: {output.get('action')}"
            target_node = payload.get("failed_task", {}).get("target_node") or payload.get("error_report", {}).get("failed_node", "v1")
            task_ids = ", ".join(t.get("task_id", "") for t in tasks if isinstance(t, dict)) if tasks else f"{target_node}_FIX"
            count_tasks = len(tasks) if tasks else 1
            return f"Plan naprawczy: {count_tasks} zadań [{task_ids}]. Diagnoza: {str(diag)[:100]}"
        tasks = output.get("tasks", [])
        blueprint = output.get("academic_blueprint") or {}
        title = blueprint.get("thesis_title") or payload.get("user_prompt", "")[:50]
        missing = output.get("missing_agent_specialization")
        task_ids = ", ".join(t.get("task_id", "") for t in tasks) if tasks else "brak"
        spec_str = f" | Wymagana nowa specjalizacja: '{missing}'" if missing else ""
        return f"Plan: {len(tasks)} zadan [{task_ids}], cel: '{title}'{spec_str}"

    # 2. Critic & audit guards
    if "critic" in name or "guard" in name or "auditor" in name:
        status = output.get("status", "PASS" if output.get("approved", True) else "FAIL")
        issues = output.get("issues", [])
        if status == "PASS" and not issues:
            return "Werdykt: PASS (Weryfikacja poprawna, brak zastrzezen)"
        issues_summary = "; ".join(str(i) for i in issues[:2])
        return f"Werdykt: {status} (Zastrzezenia: {issues_summary if issues_summary else 'wykryto bledy weryfikacji'})"

    # 3. Evolution agents
    if "evolution" in name or "architect" in name:
        # Rozpakuj response jeśli model opakował wynik w klucz 'response'
        if "response" in output and isinstance(output["response"], str):
            try:
                import json as _json
                nested = _json.loads(output["response"])
                if isinstance(nested, dict):
                    output = {**nested, **output}
            except Exception:
                pass

        # Sprawdź przypadek konsolidacji/kompakcji reguł (Rule Synthesis / Compaction)
        if "synthesized_invariant" in output or "consolidated_rules" in output:
            cnt = output.get("rules_consolidated_count", len(output.get("consolidated_rules", [])))
            inv = str(output.get("synthesized_invariant") or "")
            tgt = str(output.get("agent_id") or output.get("agent") or "agenta")
            return f"Ewolucja: KONSOLIDACJA REGUŁ ({cnt} reguł dla {tgt}: '{inv[:70]}')"

        action = output.get("action") or output.get("decision")
        if action in ("inject_rule", "apply_rule"):
            action = "MUTATE_AGENT"

        if not action or action == "UNKNOWN":
            if "injected_rule" in output or "rule" in output:
                action = "MUTATE_AGENT"
            elif "suggested_actions" in output or output.get("status") in ("FAIL", "RETRY"):
                action = "REPAIR_ANALYSIS"
            elif "specialization" in output:
                action = "CREATE_AGENT"
            elif "sub_specializations" in output:
                action = "SPLIT_AGENT"
            elif "tool_name" in output or "validator_name" in output:
                action = "CREATE_TOOL"
            else:
                action = output.get("status") or "ADAPTACJA_SYSTEMU"

        if action == "CREATE_AGENT":
            return f"Ewolucja: CREATE_AGENT (nowy agent: '{output.get('specialization')}')"
        if action == "SPLIT_AGENT":
            subs = ", ".join(str(s) for s in output.get("sub_specializations", []))
            return f"Ewolucja: SPLIT_AGENT ({output.get('agent_id')} -> [{subs}])"
        if action == "CREATE_TOOL":
            v_name = output.get("validator_name") or output.get("tool_name") or "custom_validator.py"
            return f"Ewolucja: CREATE_TOOL (synteza walidatora: '{v_name}')"
        if action == "MUTATE_AGENT":
            rule = output.get("injected_rule") or output.get("rule", "")
            tgt = output.get("agent") or output.get("agent_id") or "seed_coder"
            return f"Ewolucja: MUTATE_AGENT ({tgt}: '{rule[:80]}')"
        if action == "REPAIR_ANALYSIS":
            reason = output.get("reason") or output.get("summary") or "analiza naruszeń kontraktu"
            return f"Ewolucja: ANALIZA NAPRAWCZA ({reason[:80]})"
        if action == "HITL":
            gate = output.get("hitl_gate", "GATE")
            q = output.get("question", "")
            return f"Ewolucja: HITL ({gate}: '{q[:80]}')"
        return f"Ewolucja: {action}"

    if "consolidator" in name:
        summary = output.get("summary") or output.get("consolidated_invariant", "")
        return f"Konsolidacja regul: {summary[:100]}"

    # 4. Builder / Coder agents
    if "coder" in name or "specialist" in name:
        summary = output.get("summary", "")
        ast_edits = output.get("ast_edits", [])
        if ast_edits:
            symbols = ", ".join(str(e.get("symbol", "")) for e in ast_edits)
            return f"Kod AST: zmodyfikowano [{symbols}] ({summary[:70]})"
        return f"Kod: {summary if summary else 'Wygenerowano kod zrodlowy'}"

    # 5. Tester agents
    if "tester" in name:
        summary = output.get("summary", "")
        test_file = output.get("test_file", "test_core.py")
        csv_file = output.get("benchmark_file", "results.csv")
        return f"Testy/CSV: {test_file}, {csv_file} ({summary[:70]})"

    # 6. Writer & Researcher agents
    if "writer" in name or "researcher" in name:
        summary = output.get("summary", "")
        sections = output.get("sections", [])
        if sections:
            titles = ", ".join(str(s.get("section_title", ""))[:25] for s in sections[:2])
            return f"Praca naukowa: {len(sections)} rozdzialow [{titles}...] ({summary[:70]})"
        return f"Praca naukowa: {summary if summary else 'Opracowano tresc rozdzialu'}"

    summary = output.get("summary") or output.get("action") or output.get("status")
    if summary:
        return f"Dzialanie: {str(summary)[:100]}"
    keys = list(output.keys())[:4]
    return f"Odpowiedz z polami: {', '.join(keys)}"


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
    action_directive = (
        "\n\n=== MANDATORY ACTION DIRECTIVE ===\n"
        "Act strictly in your assigned role defined in the system prompt. Analyze the input JSON payload above.\n"
        "Output strictly a valid JSON object matching the required schema specified in your system prompt.\n"
        "DO NOT output conversational filler, commentary, summaries, or wrapper fields like 'response'.\n"
        "Output ONLY the JSON object with the exact keys required."
    )
    combined_prompt = (
        f"{system_prompt.strip()}\n\n"
        f"=== INPUT JSON PAYLOAD ===\n"
        f"{serialized_payload}"
        f"{action_directive}\n"
    )

    conn = LLMConnectionManager(provider=provider)
    active_provider = conn.resolve_provider()
    model_name = conn.resolve_model_name(active_provider, model_tier)
    logger = get_process_logger()

    start_t = time.perf_counter()
    _LLM_TELEMETRY["calls_count"] = int(_LLM_TELEMETRY["calls_count"]) + 1
    if model_name not in _LLM_TELEMETRY["models_used"]:
        _LLM_TELEMETRY["models_used"].append(model_name)

    is_network_call = False
    parsed_output: dict[str, Any]
    raw_response_str: str
    effective_provider = active_provider

    if _CUSTOM_LLM_HANDLER is not None:
        effective_provider = "custom_handler"
        parsed_output = _CUSTOM_LLM_HANDLER(system_prompt, user_payload, model_tier)
        raw_response_str = json.dumps(parsed_output, ensure_ascii=False, indent=2)

    elif active_provider in ("google", "ollama"):
        user_only_prompt = f"=== INPUT JSON PAYLOAD ===\n{serialized_payload}{action_directive}\n"
        try:
            if active_provider == "google":
                api_res = conn.call_google_gemini(
                    model_name,
                    combined_prompt,
                    system_prompt=system_prompt.strip(),
                    user_prompt=user_only_prompt,
                )
            else:
                api_res = conn.call_ollama(
                    model_name,
                    combined_prompt,
                    system_prompt=system_prompt.strip(),
                    user_prompt=user_only_prompt,
                )

            raw_response_str = api_res.get("raw_text", "{}")
            extracted = _extract_json_from_text(raw_response_str)
            if isinstance(extracted, dict):
                parsed_output = extracted
            else:
                fallback = _default_simulated_response(path.stem, system_prompt, user_payload, model_tier)
                fallback["llm_raw_text"] = raw_response_str
                parsed_output = fallback

            is_network_call = True
        except (urllib.error.URLError, TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
            logger.log_step(
                "CONNECTION_FALLBACK",
                f"Nie udało się połączyć z '{active_provider}' ({model_name}): {exc}. Przełączam na deterministyczny fallback.",
            )
            parsed_output = _default_simulated_response(path.stem, system_prompt, user_payload, model_tier)
            raw_response_str = json.dumps(parsed_output, ensure_ascii=False, indent=2)
            effective_provider = "mock"
    else:
        effective_provider = "mock"
        parsed_output = _default_simulated_response(path.stem, system_prompt, user_payload, model_tier)
        raw_response_str = json.dumps(parsed_output, ensure_ascii=False, indent=2)

    elapsed_ms = (time.perf_counter() - start_t) * 1000.0

    if is_network_call:
        _LLM_TELEMETRY["live_network_calls"] = int(_LLM_TELEMETRY["live_network_calls"]) + 1
        _LLM_TELEMETRY["total_inference_ms"] = float(_LLM_TELEMETRY["total_inference_ms"]) + elapsed_ms

    _LLM_TELEMETRY["call_log"].append(
        {
            "agent": path.stem,
            "provider": effective_provider,
            "model": model_name,
            "tier": model_tier,
            "elapsed_ms": round(elapsed_ms, 2),
        }
    )

    decision_summary = summarize_agent_decision(path.stem, user_payload, parsed_output)
    iso_ts = datetime.now(timezone.utc).isoformat()

    interaction_record = {
        "step_index": len(_LLM_TELEMETRY.get("interactions", [])) + 1,
        "timestamp": iso_ts,
        "agent": path.stem,
        "agent_md": str(path),
        "provider": effective_provider,
        "model_tier": model_tier,
        "model_name": model_name,
        "elapsed_ms": round(elapsed_ms, 2),
        "decision_summary": decision_summary,
        "system_prompt": system_prompt,
        "user_payload": user_payload,
        "combined_prompt": combined_prompt,
        "raw_response": raw_response_str,
        "parsed_output": parsed_output,
    }
    if "interactions" not in _LLM_TELEMETRY:
        _LLM_TELEMETRY["interactions"] = []
    _LLM_TELEMETRY["interactions"].append(interaction_record)

    # Real-time console visibility
    print(
        f"    -> [LLM DECISION: {path.stem}] ({effective_provider}:{model_name}, {model_tier}, {elapsed_ms:.0f} ms)\n"
        f"       Decyzja: {decision_summary}",
        flush=True,
    )
    if os.environ.get("HARNESS_VERBOSE_PROMPTS") == "1":
        prompt_lines = combined_prompt.strip().splitlines()
        resp_lines = raw_response_str.strip().splitlines()
        print(f"    +-- [PROMPT DLA AGENTA: {path.stem}] ({len(combined_prompt)} znakow):", flush=True)
        for pl in prompt_lines[:25]:
            print(f"    | {pl}", flush=True)
        if len(prompt_lines) > 25:
            print(f"    | ... [skrocono {len(prompt_lines) - 25} linii prompta]", flush=True)
        print(f"    +-- [ODPOWIEDZ ZWROCONA PRZEZ LLM] ({len(raw_response_str)} znakow):", flush=True)
        for rl in resp_lines[:25]:
            print(f"    | {rl}", flush=True)
        if len(resp_lines) > 25:
            print(f"    | ... [skrocono {len(resp_lines) - 25} linii odpowiedzi]", flush=True)
        print("    \\-- [Koniec bloku]", flush=True)

    logger.log_agent_exchange(
        agent_md=str(path),
        provider=effective_provider,
        model_tier=model_tier,
        model_name=model_name,
        system_prompt=system_prompt,
        user_payload=user_payload,
        combined_prompt=combined_prompt,
        raw_response=raw_response_str,
        parsed_output=parsed_output,
        elapsed_ms=elapsed_ms,
    )

    return {
        "status": "ok",
        "provider": effective_provider,
        "agent_md": str(path),
        "model_tier": model_tier,
        "model_name": model_name,
        "prompt_sent": combined_prompt,
        "output": parsed_output,
        "decision_summary": decision_summary,
    }

