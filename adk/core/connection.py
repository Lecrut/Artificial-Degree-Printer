from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
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
        self.provider = (provider or os.environ.get("HARNESS_PROVIDER", "auto")).lower()

    def _probe_ollama_tags(self, timeout: float = 2.0) -> tuple[bool, list[str], str | None]:
        """Quickly check if local Ollama server is reachable and list installed models."""
        ollama_generate_url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
        ollama_base = ollama_generate_url.split("/api/")[0].rstrip("/")
        ollama_tags_url = f"{ollama_base}/api/tags"
        try:
            req = urllib.request.Request(ollama_tags_url, method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                tag_data = json.loads(resp.read().decode("utf-8"))
                models = [str(m.get("name", "")) for m in tag_data.get("models", []) if isinstance(m, dict)]
                return True, models, None
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            return False, [], str(exc)

    def resolve_provider(self) -> str:
        """Determine active provider ('google', 'ollama', or 'mock')."""
        if self.provider in ("google", "ollama", "mock"):
            return self.provider
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if api_key:
            return "google"
        if os.environ.get("HARNESS_USE_OLLAMA") == "1":
            return "ollama"
        # Outside pytest unit tests, auto-detect running local Ollama server
        if "PYTEST_CURRENT_TEST" not in os.environ:
            reachable, _, _ = self._probe_ollama_tags(timeout=1.5)
            if reachable:
                return "ollama"
        return "mock"

    def resolve_model_name(self, provider: str, model_tier: str) -> str:
        """Return model identifier for the given provider and tier ('SML' or 'LRM')."""
        if provider == "google":
            if model_tier == "LRM":
                return os.environ.get("HARNESS_GOOGLE_LRM_MODEL", "gemini-2.5-pro")
            return os.environ.get("HARNESS_GOOGLE_SML_MODEL", "gemini-2.5-flash")

        if model_tier == "LRM":
            return os.environ.get(
                "HARNESS_OLLAMA_LRM_MODEL",
                os.environ.get("HARNESS_LRM_MODEL", "qwen3-coder:latest"),
            )
        return os.environ.get(
            "HARNESS_OLLAMA_SML_MODEL",
            os.environ.get("HARNESS_SML_MODEL", "gemma4:e2b"),
        )

    def call_google_gemini(
        self,
        model_name: str,
        combined_prompt: str,
        timeout: int = 300,
        system_prompt: str | None = None,
        user_prompt: str | None = None,
    ) -> dict[str, Any]:
        """Call Google Gemini generateContent REST endpoint using GEMINI_API_KEY / GOOGLE_API_KEY."""
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("Brak klucza GEMINI_API_KEY lub GOOGLE_API_KEY w zmiennych środowiskowych / .env.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload: dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt if user_prompt is not None else combined_prompt}],
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
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
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidates = data.get("candidates", [])
            text = ""
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    text = parts[0].get("text", "")
            return {"status": "ok", "raw_text": text, "raw_payload": data}

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
            return {
                "status": "ok",
                "raw_text": raw_resp.get("response", "{}"),
                "raw_payload": raw_resp,
            }

    def check_llm_access(self) -> dict[str, Any]:
        """Verify availability of Google Gemini API, local Ollama server, and Mock fallback without running benchmarks."""
        dotenv_vars = load_dotenv_file()
        resolved = self.resolve_provider()
        sml_model = self.resolve_model_name(resolved, "SML")
        lrm_model = self.resolve_model_name(resolved, "LRM")

        has_gemini_key = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))

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
        }


