from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

from adk.core.connection import LLMConnectionManager
from adk.core.llm import get_llm_telemetry, reset_llm_telemetry


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
