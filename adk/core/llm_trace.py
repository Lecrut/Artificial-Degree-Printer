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
    decision = _safe_summary(parsed_output)
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


def _issue_text(issue: Any) -> str:
    if not isinstance(issue, dict):
        return str(issue)
    mark = "BLOKUJĄCE " if issue.get("blocking") is True else ""
    return f"{mark}{issue.get('where') or ''}: {issue.get('problem') or issue}".strip(": ")


def _safe_summary(output: Any) -> str:
    """Recording an answer never stops a run: an answer of an unexpected shape gets a plain summary."""
    try:
        return summarize_agent_decision(output)
    except Exception as exc:  # noqa: BLE001 - the summary is for people; the answer itself is judged elsewhere
        return f"Odpowiedź ({type(output).__name__}); podsumowanie niedostępne: {type(exc).__name__}"


def summarize_agent_decision(output: Any) -> str:
    """One line for the console and the logs: the verdict or decision, the findings, the size of the answer.
    The whole answer is in agent_trace.jsonl; until 2026-11-18 this guessed the format of every agent (130 lines)."""
    if not isinstance(output, dict):
        return f"Wynik: {str(output)[:100]}"
    parts = [f"{key}={output[key]}" for key in ("status", "decision", "action") if output.get(key)]
    issues = output.get("issues")
    if isinstance(issues, list) and issues:
        more = f" (+{len(issues) - 2})" if len(issues) > 2 else ""
        parts.append("uwagi: " + "; ".join(_issue_text(i)[:120] for i in issues[:2]) + more)
    for key, label in (("tasks", "zadania"), ("files", "pliki"), ("ast_edits", "edycje"), ("interfaces", "interfejsy")):
        value = output.get(key)
        if isinstance(value, (list, dict)) and value:
            parts.append(f"{label}: {len(value)}")
    if output.get("summary"):
        parts.append(str(output["summary"])[:100])
    return "; ".join(parts) or "Odpowiedź z polami: " + ", ".join(list(output)[:5])
