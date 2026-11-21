from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Callable

from adk.core.connection import LLMConnectionManager
from adk.core.llm_trace import fail_call, finish_call, start_call
from adk.core.models import resolve_adk_path

# (agent name, system prompt, payload, tier) -> parsed output
AgentSimulator = Callable[[str, str, dict[str, Any], str], dict[str, Any]]
_CUSTOM_LLM_HANDLER: AgentSimulator | None = None

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


def set_llm_handler(handler: AgentSimulator | None) -> None:
    """Install (or clear with None) the agents that answer instead of a model: `handler(agent, system_prompt,
    payload, tier) -> output`. Offline simulations (`adk.mocks`) and tests use it; the harness never knows."""
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


def _parse_model_answer(agent: str, raw_response_str: str) -> dict[str, Any]:
    """The answer of a model as a dict; text that is not JSON is surfaced as a failure (never replaced by a
    simulated answer), except prose of a writer and fenced Python of a coder, which are accepted as such."""
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
        stem = agent.lower()
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
    return parsed_output


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
    effective_provider = "custom_handler" if _CUSTOM_LLM_HANDLER is not None else active_provider
    call = start_call(
        agent_md=str(path), agent=path.stem, provider=effective_provider, model_name=model_name, model_tier=model_tier,
        system_prompt=system_prompt, user_payload=user_payload, combined_prompt=combined_prompt,
    )
    api_res: dict[str, Any] = {}
    try:
        if _CUSTOM_LLM_HANDLER is not None:
            parsed_output = _CUSTOM_LLM_HANDLER(path.stem, system_prompt, user_payload, model_tier)
            raw_response_str = json.dumps(parsed_output, ensure_ascii=False, indent=2)
        elif active_provider in ("google", "ollama"):
            # The wall-clock limit covers the whole call; urlopen's own timeout only bounds a single socket
            # operation, so a stalled stream never returns.
            user_only_prompt = f"=== INPUT JSON PAYLOAD ===\n{serialized_payload}{action_directive}\n"

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

            api_res = _call_with_wall_clock_limit(_dispatch, model_name)
            if active_provider == "google" and api_res.get("model_used"):
                model_name = api_res["model_used"]
            raw_response_str = api_res.get("raw_text", "{}")
            parsed_output = _parse_model_answer(path.stem, raw_response_str)
        else:
            # Provider "mock" means: no model, simulated agents answer. They are installed from outside (adk.mocks);
            # this module never imports them, so the harness cannot depend on a simulation.
            raise RuntimeError(
                f"provider '{active_provider}' has no simulated agents installed for '{path.stem}': "
                "install them with adk.mocks.install_simulated_agents() (or set_llm_handler)"
            )
    except (TimeoutError, OSError) as exc:
        # The call failed (wall-clock limit, connection, HTTP 5xx): logged, and the caller gets an answer that says
        # so. It used to be re-raised, and one slow call ended the whole run (01, 2026-11-21).
        fail_call(call, exc)
        return {
            "status": "error", "error": str(exc)[:300], "provider": effective_provider, "agent_md": str(path),
            "model_tier": model_tier, "model_name": model_name, "output": {},
        }
    except Exception as exc:
        fail_call(call, exc)
        raise

    p_tok = int(api_res.get("prompt_tokens") or 0)
    c_tok = int(api_res.get("completion_tokens") or 0)
    decision_summary = finish_call(
        call, provider=effective_provider, model_name=model_name, raw_response=raw_response_str,
        parsed_output=parsed_output, tokens=(p_tok, c_tok, int(api_res.get("total_tokens") or (p_tok + c_tok))),
        done_reason=str(api_res.get("done_reason") or ""), network=bool(api_res),
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

