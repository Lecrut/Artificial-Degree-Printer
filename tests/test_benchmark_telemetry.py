from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

from adk.core.connection import LLMConnectionManager
from adk.core.llm_trace import get_llm_telemetry, reset_llm_telemetry


def test_ollama_token_telemetry_extraction():
    """Verify that call_ollama extracts prompt_eval_count and eval_count as tokens."""
    conn = LLMConnectionManager(provider="ollama")
    mock_resp_data = {
        "response": '{"status": "ok"}',
        "prompt_eval_count": 142,
        "eval_count": 58,
    }

    mock_urlopen = MagicMock()
    mock_urlopen.return_value.__enter__.return_value.read.return_value = json.dumps(mock_resp_data).encode("utf-8")

    with patch("urllib.request.urlopen", mock_urlopen):
        res = conn.call_ollama("mock-model", "test prompt")

    assert res["status"] == "ok"
    assert res["prompt_tokens"] == 142
    assert res["completion_tokens"] == 58
    assert res["total_tokens"] == 200


def test_llm_telemetry_token_aggregation():
    """Verify that llm telemetry correctly records and aggregates token counts across calls."""
    reset_llm_telemetry()
    initial_stats = get_llm_telemetry()
    assert initial_stats["total_tokens"] == 0
    assert initial_stats["prompt_tokens"] == 0
    assert initial_stats["completion_tokens"] == 0

def test_gemini_carousel_failover_rotates_on_429():
    """Verify that when a model in the tier pool returns 429/503, call_google_gemini dynamically rotates to the next model in the pool."""
    import urllib.error
    import io

    conn = LLMConnectionManager(provider="google")
    conn.api_key = "test-api-key"

    call_urls: list[str] = []

    def mock_urlopen(req, **_kwargs):
        url = req.full_url
        call_urls.append(url)
        if "gemini-3.6-flash" in url:
            # Model 1 returns 429 Too Many Requests
            raise urllib.error.HTTPError(url, 429, "Too Many Requests", {}, io.BytesIO(b'{"error": "rate limit"}'))
        # Model 2 succeeds
        resp = MagicMock()
        resp.__enter__.return_value.read.return_value = json.dumps({
            "candidates": [{"content": {"parts": [{"text": '{"result": "success"}'}]}}],
            "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 20, "totalTokenCount": 30}
        }).encode("utf-8")
        return resp

    with patch.dict(os.environ, {"HARNESS_GOOGLE_LRM_MODELS": "gemini-3.6-flash,gemini-3-flash-preview"}):
        with patch("urllib.request.urlopen", side_effect=mock_urlopen):
            res = conn.call_google_gemini("gemini-3.6-flash", "test prompt", model_tier="LRM")

    assert res["status"] == "ok"
    assert res["model_used"] == "gemini-3-flash-preview"
    assert "gemini-3.6-flash" in call_urls[0]
    assert "gemini-3-flash-preview" in call_urls[1]


def test_every_agent_call_is_logged_before_and_after_it_runs(tmp_path):
    """Simulated or real, each call leaves LLM_CALL_START/END (with the decision) in events.jsonl, its payload in
    agent_trace.jsonl before the answer, and an error record when it fails. Until 2026-11-18 only network calls
    reached events.jsonl, so a plan critic that never ran was indistinguishable from one that was not logged."""
    from adk.core.llm import call_agent, set_llm_handler
    from adk.core.logger import set_process_log_dir
    from adk.core.models import resolve_adk_path

    critic = resolve_adk_path("agents/planning/plan_critic_guard.md")
    seen_payloads: list[dict] = []

    def agents(agent, _system_prompt, payload, _tier):
        trace = (tmp_path / "agent_trace.jsonl").read_text(encoding="utf-8").splitlines()
        seen_payloads.append(json.loads(trace[-1]))  # what was already on disk while the agent was thinking
        if payload.get("boom"):
            raise TimeoutError("model hung")
        return {"status": "FAIL", "issues": [{"where": "core.py", "problem": "no seeds", "blocking": True}]} if agent == "plan_critic_guard" else {}

    set_process_log_dir(tmp_path)
    set_llm_handler(agents)
    reset_llm_telemetry()
    try:
        out = call_agent(critic, {"tasks": [], "interfaces": {"core.py": "x = 1\n"}}, model_tier="LRM", provider="mock")
        failed = call_agent(critic, {"boom": True}, model_tier="LRM", provider="mock")  # returned, not raised (§XVI.7)
    finally:
        set_llm_handler(None)
        set_process_log_dir(None)

    assert failed["status"] == "error" and "model hung" in failed["error"] and failed["output"] == {}
    assert seen_payloads[0]["phase"] == "request" and seen_payloads[0]["user_payload"]["interfaces"] == {"core.py": "x = 1\n"}
    assert "BLOKUJĄCE core.py: no seeds" in out["decision_summary"]
    events = [json.loads(line) for line in (tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    calls = [(e["event"], e["step"], e.get("ok")) for e in events if e["event"].startswith("LLM_CALL")]
    assert calls == [("LLM_CALL_START", 1, None), ("LLM_CALL_END", 1, True), ("LLM_CALL_START", 2, None), ("LLM_CALL_END", 2, False)]
    end = next(e for e in events if e["event"] == "LLM_CALL_END")
    assert end["agent"] == "plan_critic_guard" and end["verdict"] == "FAIL" and "no seeds" in end["decision"]
    phases = [json.loads(line)["phase"] for line in (tmp_path / "agent_trace.jsonl").read_text(encoding="utf-8").splitlines()]
    assert phases == ["request", "answer", "request", "error"]
    assert get_llm_telemetry()["calls_count"] == 2 and len(get_llm_telemetry()["interactions"]) == 1
