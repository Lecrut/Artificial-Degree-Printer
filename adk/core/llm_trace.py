"""What is recorded about one agent call, kept apart from making the call (llm.py) and from the files (logger.py).

Every call, to a model or to simulated agents, leaves:
- before it is made: `LLM_CALL_START` in events.jsonl and harness_process.log, and a `request` record with the full
  payload in agent_trace.jsonl, so a run that dies inside a call still shows what the agent was given;
- after it: an `answer` record (prompt, raw and parsed answer) in agent_trace.jsonl and harness_process.log,
  `LLM_CALL_END` with the decision and verdict in events.jsonl, the decision on the console, and the interaction in
  the in-memory telemetry exported per benchmark task (llm_interactions.md / .jsonl);
- when it fails: `LLM_CALL_END` with ok=false and an `error` record.
Until 2026-11-18 only network calls reached events.jsonl and nothing was written before the answer came back.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from adk.core.logger import get_process_logger

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


@dataclass
class AgentCall:
    step: int
    agent: str
    agent_md: str
    provider: str
    model_name: str
    model_tier: str
    task_id: str | None
    system_prompt: str
    user_payload: dict[str, Any]
    combined_prompt: str
    started: float = field(default_factory=time.perf_counter)


def _task_id(payload: dict[str, Any]) -> str | None:
    task = payload.get("task") if isinstance(payload, dict) else None
    task = task if isinstance(task, dict) else payload.get("failed_task") if isinstance(payload, dict) else None
    return str(task["task_id"]) if isinstance(task, dict) and task.get("task_id") else None


def start_call(
    *, agent_md: str, agent: str, provider: str, model_name: str, model_tier: str, system_prompt: str,
    user_payload: dict[str, Any], combined_prompt: str,
) -> AgentCall:
    _LLM_TELEMETRY["calls_count"] = int(_LLM_TELEMETRY["calls_count"]) + 1
    if model_name not in _LLM_TELEMETRY["models_used"]:
        _LLM_TELEMETRY["models_used"].append(model_name)
    call = AgentCall(
        step=int(_LLM_TELEMETRY["calls_count"]), agent=agent, agent_md=agent_md, provider=provider,
        model_name=model_name, model_tier=model_tier, task_id=_task_id(user_payload), system_prompt=system_prompt,
        user_payload=user_payload, combined_prompt=combined_prompt,
    )
    logger = get_process_logger()
    logger.log_step(
        "LLM_CALL_START", f"#{call.step} {agent} -> {model_name} ({model_tier}, {provider})",
        {"task_id": call.task_id, "payload_keys": sorted(user_payload), "prompt_chars": len(combined_prompt)},
    )
    logger.log_event(
        "LLM_CALL_START", step=call.step, agent=agent, model=model_name, tier=model_tier, provider=provider,
        task_id=call.task_id, payload_keys=sorted(user_payload), prompt_chars=len(combined_prompt),
    )
    logger.log_trace({
        "timestamp": datetime.now(timezone.utc).isoformat(), "phase": "request", "step": call.step,
        "agent_md": agent_md, "provider": provider, "model_tier": model_tier, "model_name": model_name,
        "user_payload": user_payload,
    })
    return call


def finish_call(
    call: AgentCall, *, provider: str, model_name: str, raw_response: str, parsed_output: dict[str, Any],
    tokens: tuple[int, int, int] = (0, 0, 0), done_reason: str = "", network: bool = False,
) -> str:
    """Record the answer; returns the one-line decision summary."""
    elapsed_ms = (time.perf_counter() - call.started) * 1000.0
    p_tok, c_tok, t_tok = tokens
    if network:
        _LLM_TELEMETRY["live_network_calls"] = int(_LLM_TELEMETRY["live_network_calls"]) + 1
        _LLM_TELEMETRY["total_inference_ms"] = float(_LLM_TELEMETRY["total_inference_ms"]) + elapsed_ms
        _LLM_TELEMETRY["prompt_tokens"] = int(_LLM_TELEMETRY["prompt_tokens"]) + p_tok
        _LLM_TELEMETRY["completion_tokens"] = int(_LLM_TELEMETRY["completion_tokens"]) + c_tok
        _LLM_TELEMETRY["total_tokens"] = int(_LLM_TELEMETRY["total_tokens"]) + t_tok
    _LLM_TELEMETRY["call_log"].append({
        "agent": call.agent, "provider": provider, "model": model_name, "tier": call.model_tier,
        "elapsed_ms": round(elapsed_ms, 2), "prompt_tokens": p_tok, "completion_tokens": c_tok, "total_tokens": t_tok,
    })
    decision = summarize_agent_decision(call.agent, call.user_payload, parsed_output)
    _LLM_TELEMETRY["interactions"].append({
        "step_index": call.step,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": call.agent,
        "agent_md": call.agent_md,
        "provider": provider,
        "model_tier": call.model_tier,
        "model_name": model_name,
        "elapsed_ms": round(elapsed_ms, 2),
        "prompt_tokens": p_tok,
        "completion_tokens": c_tok,
        "total_tokens": t_tok,
        "done_reason": done_reason,
        "decision_summary": decision,
        "system_prompt": call.system_prompt,
        "user_payload": call.user_payload,
        "combined_prompt": call.combined_prompt,
        "raw_response": raw_response,
        "parsed_output": parsed_output,
    })

    logger = get_process_logger()
    logger.log_event(
        "LLM_CALL_END", step=call.step, agent=call.agent, model=model_name, tier=call.model_tier, task_id=call.task_id,
        ok=True, elapsed_s=round(elapsed_ms / 1000.0, 1), done_reason=done_reason or None,
        verdict=parsed_output.get("status") if isinstance(parsed_output, dict) else None, decision=decision,
    )
    logger.log_agent_exchange(
        step=call.step, agent_md=call.agent_md, provider=provider, model_tier=call.model_tier, model_name=model_name,
        system_prompt=call.system_prompt, user_payload=call.user_payload, combined_prompt=call.combined_prompt,
        raw_response=raw_response, parsed_output=parsed_output, elapsed_ms=elapsed_ms,
    )
    _print_decision(call, provider, model_name, elapsed_ms, decision, raw_response)
    return decision


def fail_call(call: AgentCall, exc: BaseException) -> None:
    elapsed_s = round(time.perf_counter() - call.started, 1)
    error = f"{type(exc).__name__}: {exc}"
    logger = get_process_logger()
    logger.log_event(
        "LLM_CALL_END", step=call.step, agent=call.agent, model=call.model_name, tier=call.model_tier,
        task_id=call.task_id, ok=False, elapsed_s=elapsed_s, error=error[:300],
    )
    logger.log_step("LLM_PROVIDER_ERROR", f"#{call.step} {call.agent} ({call.provider}, {call.model_name}): {error}")
    logger.log_trace({
        "timestamp": datetime.now(timezone.utc).isoformat(), "phase": "error", "step": call.step,
        "agent_md": call.agent_md, "provider": call.provider, "model_name": call.model_name, "error": error,
    })
    print(f"  [LLM BLAD] {call.agent} ({call.provider}, {call.model_name}): {error}", flush=True)


def _print_decision(call: AgentCall, provider: str, model_name: str, elapsed_ms: float, decision: str, raw: str) -> None:
    print(
        f"    -> [LLM DECISION #{call.step}: {call.agent}] ({provider}:{model_name}, {call.model_tier}, {elapsed_ms:.0f} ms)\n"
        f"       Decyzja: {decision}",
        flush=True,
    )
    if os.environ.get("HARNESS_VERBOSE_PROMPTS") != "1":
        return
    for title, text in (("PROMPT DLA AGENTA", call.combined_prompt), ("ODPOWIEDZ ZWROCONA PRZEZ LLM", raw)):
        lines = text.strip().splitlines()
        print(f"    +-- [{title}: {call.agent}] ({len(text)} znakow):", flush=True)
        for line in lines[:25]:
            print(f"    | {line}", flush=True)
        if len(lines) > 25:
            print(f"    | ... [skrocono {len(lines) - 25} linii]", flush=True)
    print("    \\-- [Koniec bloku]", flush=True)


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
        def _issue(i: Any) -> str:
            if not isinstance(i, dict):
                return str(i)
            mark = "BLOKUJĄCE " if i.get("blocking") is True else ""
            return f"{mark}{i.get('where') or ''}: {i.get('problem') or i}".strip(": ")

        issues_summary = "; ".join(_issue(i) for i in issues[:2])
        more = f" (+{len(issues) - 2})" if len(issues) > 2 else ""
        return f"Werdykt: {status} (Zastrzezenia: {issues_summary or 'wykryto bledy weryfikacji'}{more})"

    # 3. Evolution agents
    if "evolution" in name or "architect" in name:
        # Rozpakuj response jeśli model opakował wynik w klucz 'response'
        if "response" in output and isinstance(output["response"], str):
            try:
                nested = json.loads(output["response"])
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
