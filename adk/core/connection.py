"""Connection Manager for ADK LLM Providers (Google Gemini API & Local Ollama).

Implements single-point connection handling, endpoint health probes, and model selection.
Ensures offline safety: unit tests run via local Ollama or deterministic fallback without external network calls.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
import time
from pathlib import Path
from typing import Any


def load_dotenv_file(dotenv_path: str | Path | None = None) -> dict[str, str]:
    """Load key=value pairs from .env into os.environ without external dependencies."""
    candidates: list[Path] = []
    if dotenv_path:
        candidates.append(Path(dotenv_path))
    else:
        adk_root = Path(__file__).resolve().parent.parent
        repo_root = adk_root.parent
        candidates.extend([repo_root / ".env", adk_root / ".env"])

    loaded: dict[str, str] = {}
    for path in candidates:
        if not path.exists():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val
            loaded[key] = val
    return loaded


class LLMConnectionManager:
    """Unified connector for Google Gemini API, local Ollama, and deterministic fallback."""

    def __init__(self, provider: str | None = None) -> None:
        load_dotenv_file()
        self.provider = (provider or os.environ.get("HARNESS_PROVIDER", "auto")).strip().lower()
        self.api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")

    def _probe_ollama_tags(self, timeout: float = 2.0) -> tuple[bool, list[str], str | None]:
        """Quickly check if local Ollama server is reachable and list installed models."""
        ollama_generate_url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
        ollama_base = ollama_generate_url.split("/api/")[0].rstrip("/")
        ollama_tags_url = f"{ollama_base}/api/tags"
        try:
            req = urllib.request.Request(ollama_tags_url, method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [str(m.get("name", "")) for m in data.get("models", []) if isinstance(m, dict) and m.get("name")]
                return True, models, None
        except Exception as exc:
            return False, [], str(exc)

    def resolve_provider(self) -> str:
        """Determine active provider ('google', 'ollama', or 'mock')."""
        if self.provider in ("google", "ollama", "mock"):
            return self.provider

        if self.api_key:
            return "google"

        if os.environ.get("HARNESS_USE_OLLAMA") == "1":
            return "ollama"

        # Outside pytest unit tests, auto-detect running local Ollama server
        if "PYTEST_CURRENT_TEST" not in os.environ:
            reachable, _, _ = self._probe_ollama_tags(timeout=1.5)
            if reachable:
                return "ollama"

        return "mock"

    def resolve_active_provider(self) -> str:
        return self.resolve_provider()

    def resolve_model_name(self, provider: str, model_tier: str) -> str:
        """Return model identifier for the given provider and tier ('SML' or 'LRM')."""
        tier_upper = model_tier.upper()
        if provider == "google":
            if tier_upper == "LRM":
                return os.environ.get("HARNESS_GOOGLE_LRM_MODEL", "gemini-2.5-pro")
            return os.environ.get("HARNESS_GOOGLE_SML_MODEL", "gemini-2.5-flash")
        elif provider == "ollama":
            if tier_upper == "LRM":
                return os.environ.get(
                    "HARNESS_OLLAMA_LRM_MODEL",
                    "qwen3-coder:latest",
                )
            return os.environ.get(
                "HARNESS_OLLAMA_SML_MODEL",
                "gemma4:e2b",
            )
        else:
            return f"mock-{model_tier.lower()}"

    def select_model_for_tier(self, tier: str, active_provider: str) -> str:
        return self.resolve_model_name(active_provider, tier)

    def call_google_gemini(
        self,
        model_name: str,
        combined_prompt: str,
        timeout: int = 180,
        system_prompt: str | None = None,
        user_prompt: str | None = None,
    ) -> dict[str, Any]:
        """Call Google Gemini Generative Language API via standard library urllib."""
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable is not set")

        clean_model = model_name if model_name.startswith("models/") else f"models/{model_name}"
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/{clean_model}:generateContent"
            f"?key={self.api_key}"
        )

        user_content = user_prompt if user_prompt is not None else combined_prompt
        payload: dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_content}],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
        }
        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}],
            }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        max_retries = 3
        last_exc: Exception | None = None
        for attempt in range(max_retries):
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    candidates = data.get("candidates", [])
                    text = ""
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            text = parts[0].get("text", "")
                    usage = data.get("usageMetadata", {})
                    p_tok = int(usage.get("promptTokenCount") or 0)
                    c_tok = int(usage.get("candidatesTokenCount") or 0)
                    t_tok = int(usage.get("totalTokenCount") or (p_tok + c_tok))
                    return {
                        "status": "ok",
                        "raw_text": text,
                        "raw_payload": data,
                        "prompt_tokens": p_tok,
                        "completion_tokens": c_tok,
                        "total_tokens": t_tok,
                    }
            except urllib.error.HTTPError as err:
                last_exc = err
                # 503 Service Unavailable / 429 Too Many Requests -> retry with backoff
                if err.code in (503, 429) and attempt < max_retries - 1:
                    sleep_s = 2.0 * (attempt + 1)
                    time.sleep(sleep_s)
                    continue
                raise
            except Exception as err:
                last_exc = err
                raise
        if last_exc:
            raise last_exc

    def call_ollama(
        self,
        model_name: str,
        combined_prompt: str,
        timeout: int = 300,
        system_prompt: str | None = None,
        user_prompt: str | None = None,
    ) -> dict[str, Any]:
        """Call local Ollama /api/generate endpoint."""
        ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
        body_dict: dict[str, Any] = {
            "model": model_name,
            "prompt": user_prompt if user_prompt is not None else combined_prompt,
            "stream": False,
            "format": "json",
        }
        if system_prompt:
            body_dict["system"] = system_prompt
        req_body = json.dumps(body_dict).encode("utf-8")
        req = urllib.request.Request(
            ollama_url,
            data=req_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw_resp = json.loads(resp.read().decode("utf-8"))
            p_tok = int(raw_resp.get("prompt_eval_count") or 0)
            c_tok = int(raw_resp.get("eval_count") or 0)
            t_tok = p_tok + c_tok
            return {
                "status": "ok",
                "raw_text": raw_resp.get("response", "{}"),
                "raw_payload": raw_resp,
                "prompt_tokens": p_tok,
                "completion_tokens": c_tok,
                "total_tokens": t_tok,
            }

    def check_llm_access(self) -> dict[str, Any]:
        """Verify availability of Google Gemini API, local Ollama server, and Mock fallback without running benchmarks."""
        dotenv_vars = load_dotenv_file()
        resolved = self.resolve_provider()
        sml_model = self.resolve_model_name(resolved, "SML")
        lrm_model = self.resolve_model_name(resolved, "LRM")

        has_gemini_key = bool(self.api_key)
        ollama_generate_url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
        ollama_reachable, ollama_models, ollama_error = self._probe_ollama_tags(timeout=3.0)

        return {
            "configured_provider": self.provider,
            "resolved_provider": resolved,
            "sml_model": sml_model,
            "lrm_model": lrm_model,
            "dotenv_loaded": bool(dotenv_vars),
            "google_api_key_present": has_gemini_key,
            "ollama": {
                "url": ollama_generate_url,
                "reachable": ollama_reachable,
                "installed_models": ollama_models,
                "error": ollama_error,
            },
            "mock": {
                "available": True,
                "description": "Deterministic internal mock with AST templates and instant response.",
            },
        }

    def test_connection_endpoints(self) -> dict[str, Any]:
        return self.check_llm_access()
