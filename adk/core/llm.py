from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from adk.core.connection import LLMConnectionManager
from adk.core.logger import get_process_logger
from adk.core.models import resolve_adk_path

_CUSTOM_LLM_HANDLER: Callable[[str, dict[str, Any], str], dict[str, Any]] | None = None

# Wall-clock budget for one whole model call. The per-request socket timeout does not bound a stalled stream.
LLM_WALL_CLOCK_LIMIT_S = int(os.environ.get("HARNESS_LLM_WALL_CLOCK_LIMIT_S", "600"))


def _call_with_wall_clock_limit(dispatch: Callable[[], dict[str, Any]], model_name: str) -> dict[str, Any]:
    """Run `dispatch` in a daemon thread and give up after LLM_WALL_CLOCK_LIMIT_S with a TimeoutError, so a
    hung provider ends as a logged failure of one call instead of silently freezing the whole run."""
    import threading

    box: dict[str, Any] = {}

    def _run() -> None:
        try:
            box["result"] = dispatch()
        except BaseException as exc:  # noqa: BLE001 - re-raised in the caller thread
            box["error"] = exc

    worker = threading.Thread(target=_run, daemon=True)
    worker.start()
    worker.join(LLM_WALL_CLOCK_LIMIT_S)
    if worker.is_alive():
        raise TimeoutError(
            f"Wywołanie modelu {model_name} nie zakończyło się w {LLM_WALL_CLOCK_LIMIT_S}s (limit zegarowy całego wywołania)."
        )
    if "error" in box:
        raise box["error"]
    return box["result"]
_LLM_TELEMETRY: dict[str, Any] = {
    "calls_count": 0,
    "live_network_calls": 0,
    "total_inference_ms": 0.0,
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0,
    "models_used": [],
    "call_log": [],
    "interactions": [],
}


def reset_llm_telemetry() -> None:
    """Reset per-task LLM call counters, timing metrics, and full interaction records."""
    _LLM_TELEMETRY["calls_count"] = 0
    _LLM_TELEMETRY["live_network_calls"] = 0
    _LLM_TELEMETRY["total_inference_ms"] = 0.0
    _LLM_TELEMETRY["prompt_tokens"] = 0
    _LLM_TELEMETRY["completion_tokens"] = 0
    _LLM_TELEMETRY["total_tokens"] = 0
    _LLM_TELEMETRY["models_used"] = []
    _LLM_TELEMETRY["call_log"] = []
    _LLM_TELEMETRY["interactions"] = []


def get_llm_telemetry() -> dict[str, Any]:
    """Return a snapshot of LLM call counts, network inference time, models used, and full interactions."""
    return {
        "calls_count": int(_LLM_TELEMETRY["calls_count"]),
        "live_network_calls": int(_LLM_TELEMETRY["live_network_calls"]),
        "total_inference_ms": round(float(_LLM_TELEMETRY["total_inference_ms"]), 2),
        "prompt_tokens": int(_LLM_TELEMETRY.get("prompt_tokens", 0)),
        "completion_tokens": int(_LLM_TELEMETRY.get("completion_tokens", 0)),
        "total_tokens": int(_LLM_TELEMETRY.get("total_tokens", 0)),
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
        # Logged BEFORE the call: when a run dies inside a model call, the log must show which one (the
        # 2026-11-14 run ended with no trace of what it was waiting for). The wall-clock limit covers the whole
        # call; urlopen's own timeout only bounds a single socket operation, so a stalled stream never returns.
        task_ref = user_payload.get("task") if isinstance(user_payload, dict) else None
        task_id = task_ref.get("task_id") if isinstance(task_ref, dict) else None
        logger.log_step(
            "LLM_CALL_START",
            f"{path.stem} -> {model_name} ({model_tier}, {active_provider})",
            {"prompt_chars": len(combined_prompt)},
        )
        try:
            def _dispatch() -> dict[str, Any]:
                if active_provider == "google":
                    return conn.call_google_gemini(
                        model_name,
                        combined_prompt,
                        system_prompt=system_prompt.strip(),
                        user_prompt=user_only_prompt,
                        model_tier=model_tier,
                    )
                return conn.call_ollama(
                    model_name,
                    combined_prompt,
                    system_prompt=system_prompt.strip(),
                    user_prompt=user_only_prompt,
                    model_tier=model_tier,
                )

            logger.log_event("LLM_CALL_START", agent=path.stem, model=model_name, tier=model_tier, task_id=task_id)
            api_res = _call_with_wall_clock_limit(_dispatch, model_name)
            logger.log_event(
                "LLM_CALL_END", agent=path.stem, model=model_name, tier=model_tier, task_id=task_id, ok=True,
                elapsed_s=round(time.perf_counter() - start_t, 1), done_reason=api_res.get("done_reason"),
            )
            if active_provider == "google" and api_res.get("model_used"):
                model_name = api_res["model_used"]

            raw_response_str = api_res.get("raw_text", "{}")
            extracted = _extract_json_from_text(raw_response_str)
            if isinstance(extracted, dict):
                parsed_output = extracted
            else:
                # In live LLM runs (Ollama, Gemini), NEVER inject simulated mock responses!
                # Surface genuine LLM raw text so Layer 3 supervisors can evaluate real output.
                parsed_output = {
                    "raw_response": raw_response_str,
                    "error": "Failed to parse JSON from LLM response",
                    "status": "FAIL",
                    "issues": [f"Model returned non-JSON format: {raw_response_str[:120]}..."],
                }
                stem = path.stem.lower()
                if any(w in stem for w in ("writer", "researcher", "sota")):
                    # Only accept raw response if it is actual markdown prose and not broken JSON
                    stripped_raw = raw_response_str.strip()
                    if stripped_raw and not stripped_raw.startswith(("{", "[")):
                        parsed_output["section_content"] = stripped_raw
                        parsed_output["content"] = stripped_raw
                        parsed_output["status"] = "PASS"
                elif any(c in stem for c in ("coder", "tester")):
                    # Try to extract valid python code from markdown fences ```python ... ```
                    code_match = re.search(
                        r"```(?:python)?\s*\n(.*?)```",
                        raw_response_str,
                        flags=re.DOTALL | re.IGNORECASE,
                    )
                    candidate_code = code_match.group(1).strip() if code_match else None
                    if candidate_code:
                        try:
                            import ast
                            ast.parse(candidate_code)
                            parsed_output["source_code"] = candidate_code
                            parsed_output["status"] = "PASS"
                            parsed_output.pop("error", None)
                            parsed_output.pop("issues", None)
                        except Exception:
                            # Not valid Python - remains FAIL so Layer 3 / Gate 3 catches it
                            pass

            call_prompt_tokens = int(api_res.get("prompt_tokens") or 0)
            call_completion_tokens = int(api_res.get("completion_tokens") or 0)
            call_total_tokens = int(api_res.get("total_tokens") or (call_prompt_tokens + call_completion_tokens))
            is_network_call = True
        except Exception as exc:
            logger.log_event(
                "LLM_CALL_END", agent=path.stem, model=model_name, tier=model_tier, ok=False,
                task_id=task_id,
                elapsed_s=round(time.perf_counter() - start_t, 1), error=f"{type(exc).__name__}: {exc}"[:300],
            )
            logger.log_step(
                "LLM_PROVIDER_ERROR",
                f"Blad wywolania dostawcy '{active_provider}' ({model_name}): {exc}",
            )
            print(f"  [LLM BLAD SIECIOWY] Nie udalo sie pobrac odpowiedzi z dostawcy '{active_provider}' ({model_name}): {exc}", flush=True)
            raise
    else:
        effective_provider = "mock"
        from adk.mocks.default_responses import default_simulated_response

        parsed_output = default_simulated_response(path.stem, system_prompt, user_payload, model_tier)
        raw_response_str = json.dumps(parsed_output, ensure_ascii=False, indent=2)

    elapsed_ms = (time.perf_counter() - start_t) * 1000.0

    p_tok = call_prompt_tokens if is_network_call else 0
    c_tok = call_completion_tokens if is_network_call else 0
    t_tok = call_total_tokens if is_network_call else 0

    if is_network_call:
        _LLM_TELEMETRY["live_network_calls"] = int(_LLM_TELEMETRY["live_network_calls"]) + 1
        _LLM_TELEMETRY["total_inference_ms"] = float(_LLM_TELEMETRY["total_inference_ms"]) + elapsed_ms
        _LLM_TELEMETRY["prompt_tokens"] = int(_LLM_TELEMETRY.get("prompt_tokens", 0)) + p_tok
        _LLM_TELEMETRY["completion_tokens"] = int(_LLM_TELEMETRY.get("completion_tokens", 0)) + c_tok
        _LLM_TELEMETRY["total_tokens"] = int(_LLM_TELEMETRY.get("total_tokens", 0)) + t_tok

    _LLM_TELEMETRY["call_log"].append(
        {
            "agent": path.stem,
            "provider": effective_provider,
            "model": model_name,
            "tier": model_tier,
            "elapsed_ms": round(elapsed_ms, 2),
            "prompt_tokens": p_tok,
            "completion_tokens": c_tok,
            "total_tokens": t_tok,
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
        "prompt_tokens": p_tok,
        "completion_tokens": c_tok,
        "total_tokens": t_tok,
        "done_reason": str(api_res.get("done_reason") or "") if is_network_call else "",
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

