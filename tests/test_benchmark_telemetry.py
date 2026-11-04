from __future__ import annotations

import json
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
