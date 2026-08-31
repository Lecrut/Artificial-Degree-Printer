from __future__ import annotations

import json
import os
import urllib.request
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LLMMessage(BaseModel):
    role: str = Field(..., description="Rola: system, user, assistant")
    content: str = Field(..., description="Treść wiadomości")


class LLMResponse(BaseModel):
    content: str = Field(..., description="Wygenerowana odpowiedź")
    model_name: str = Field(default="fallback-engine", description="Użyty model")
    prompt_tokens: int = Field(default=0, description="Liczba tokenów wejściowych")
    completion_tokens: int = Field(default=0, description="Liczba tokenów wyjściowych")


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, messages: List[LLMMessage], **kwargs: Any) -> LLMResponse:
        raise NotImplementedError


class FallbackDeterministicProvider(BaseLLMProvider):
    def generate(self, messages: List[LLMMessage], **kwargs: Any) -> LLMResponse:
        user_msg = next((m.content for m in reversed(messages) if m.role == "user"), "")
        return LLMResponse(
            content=f"Syntetyczna odpowiedź analityczna dla: {user_msg[:100]}...",
            model_name="adk-deterministic-core-2027",
            prompt_tokens=len(user_msg.split()),
            completion_tokens=50,
        )


class OllamaLocalProvider(BaseLLMProvider):
    """
    100% Offline Local LLM Provider via Ollama API (http://localhost:11434).
    Supports models like qwen2.5-coder, llama3.3, deepseek-r1, mistral.
    """
    def __init__(self, model_name: str = "qwen2.5-coder:7b", host: str = "http://localhost:11434") -> None:
        self.model_name = model_name
        self.host = host.rstrip("/")

    def generate(self, messages: List[LLMMessage], **kwargs: Any) -> LLMResponse:
        url = f"{self.host}/api/chat"
        payload = {
            "model": self.model_name,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                content = result.get("message", {}).get("content", "")
                return LLMResponse(
                    content=content,
                    model_name=f"ollama/{self.model_name}",
                    prompt_tokens=result.get("prompt_eval_count", 0),
                    completion_tokens=result.get("eval_count", 0),
                )
        except Exception as e:
            return LLMResponse(
                content=f"[Ollama Fallback] Błąd połączenia z lokalnym silnikiem Ollama ({self.host}): {str(e)}",
                model_name=f"ollama/{self.model_name}",
            )


class GoogleGeminiProvider(BaseLLMProvider):
    """
    Google Gemini Cloud API Provider (Gemini 2.5 Pro / Flash).
    Requires GEMINI_API_KEY or GOOGLE_API_KEY environment variable.
    """
    def __init__(self, model_name: str = "gemini-2.5-pro", api_key: Optional[str] = None) -> None:
        self.model_name = model_name
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    def generate(self, messages: List[LLMMessage], **kwargs: Any) -> LLMResponse:
        if not self.api_key:
            return LLMResponse(
                content="[Gemini Provider] Brak klucza GEMINI_API_KEY w środowisku. Uzupełnij plik .env lub przełącz na provider 'ollama'.",
                model_name=self.model_name,
            )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        
        contents = []
        for m in messages:
            role = "user" if m.role in ("user", "system") else "model"
            contents.append({"role": role, "parts": [{"text": m.content}]})

        payload = {"contents": contents}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                return LLMResponse(
                    content=text,
                    model_name=f"google/{self.model_name}",
                )
        except Exception as e:
            return LLMResponse(
                content=f"[Gemini Provider Error] Błąd wywołania API Gemini: {str(e)}",
                model_name=self.model_name,
            )


class OpenAICompatibleProvider(BaseLLMProvider):
    """
    OpenAI / vLLM / LM Studio Compatible Provider.
    Requires OPENAI_API_KEY or custom base_url.
    """
    def __init__(self, model_name: str = "gpt-4o", base_url: str = "https://api.openai.com/v1", api_key: Optional[str] = None) -> None:
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")

    def generate(self, messages: List[LLMMessage], **kwargs: Any) -> LLMResponse:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        req = urllib.request.Request(url, data=data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                content = result["choices"][0]["message"]["content"]
                usage = result.get("usage", {})
                return LLMResponse(
                    content=content,
                    model_name=f"openai/{self.model_name}",
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                )
        except Exception as e:
            return LLMResponse(
                content=f"[OpenAI Provider Error] Błąd połączenia ({self.base_url}): {str(e)}",
                model_name=self.model_name,
            )


class HeterogeneousRouterLLMClient:
    """
    SOTA Multi-Agent Heterogeneous Model Router (ACRouter 2026):
    Routes each agent role (orchestrator, developer, typesetter, etc.)
    to its optimal specialized model for maximum quality and speed.
    """
    def __init__(self, mode: str = "hybrid") -> None:
        self.mode = mode
        # Domyślny rozkład hybrydowy (Ollama local RTX 5070 8GB + Google Gemini Pro)
        self.role_providers: Dict[str, BaseLLMProvider] = {
            "orchestrator": GoogleGeminiProvider(model_name="gemini-2.5-pro"),
            "researcher": GoogleGeminiProvider(model_name="gemini-2.5-flash"),
            "architect": GoogleGeminiProvider(model_name="gemini-2.5-pro"),
            "developer": OllamaLocalProvider(model_name="qwen2.5-coder:7b"),
            "experimenter": GoogleGeminiProvider(model_name="gemini-2.5-flash"),
            "typesetter": GoogleGeminiProvider(model_name="gemini-2.5-pro"),
            "reviewer": GoogleGeminiProvider(model_name="gemini-2.5-pro"),
        }

    def estimate_task_complexity(self, prompt: str) -> float:
        """Estimates task complexity score chi(T) in range [0.0, 1.0] based on prompt cues."""
        score = 0.1
        prompt_len = len(prompt)
        
        # Length-based complexity bounds
        if prompt_len > 5000:
            score += 0.3
        elif prompt_len > 2000:
            score += 0.15
            
        # Semantic keywords checks
        complexity_keywords = [
            "architect", "c4", "architecture", "typeset", "thesis", "latex", "typst",
            "verify", "stylometry", "cross_consistency", "replan", "mutation"
        ]
        coding_keywords = ["implement", "function", "class", "code", "module", "parse"]
        
        lower_prompt = prompt.lower()
        complexity_matches = sum(1 for kw in complexity_keywords if kw in lower_prompt)
        if complexity_matches > 0:
            score += min(0.6, complexity_matches * 0.15 + 0.25)
        
        coding_matches = sum(1 for kw in coding_keywords if kw in lower_prompt)
        if coding_matches > 0 and complexity_matches == 0:
            score += min(0.4, coding_matches * 0.1 + 0.15)
            
        return min(1.0, score)

    def get_provider_for_agent(self, agent_name: str, complexity: Optional[float] = None) -> BaseLLMProvider:
        if complexity is None:
            role = agent_name.lower().replace("agent", "").strip()
            return self.role_providers.get(role, GoogleGeminiProvider(model_name="gemini-2.5-flash"))
        # Route to Tier 3 for complex tasks, Tier 2 for coding, and Tier 1 for simple tasks
        if complexity >= 0.70:
            return GoogleGeminiProvider(model_name="gemini-2.5-pro")
        elif complexity >= 0.35:
            return OllamaLocalProvider(model_name="qwen2.5-coder:7b")
        else:
            return GoogleGeminiProvider(model_name="gemini-2.5-flash")

    def complete_for_agent(self, agent_name: str, prompt: str, system_prompt: Optional[str] = None) -> str:
        complexity = self.estimate_task_complexity(prompt)
        provider = self.get_provider_for_agent(agent_name, complexity)
        
        # Log Topaz routing rationale
        tier = "Tier 3 (Cloud Pro)" if complexity >= 0.70 else ("Tier 2 (Local SLM)" if complexity >= 0.35 else "Tier 1 (Cloud Flash)")
        print(f"[Topaz Router] Routed agent '{agent_name}' to {tier} (Model: {provider.model_name}) based on complexity score: {complexity:.2f}")

        messages: List[LLMMessage] = []
        if system_prompt:
            messages.append(LLMMessage(role="system", content=system_prompt))
        messages.append(LLMMessage(role="user", content=prompt))

        resp = provider.generate(messages)
        return resp.content


class LLMClient:
    """
    Unified ADK LLM Client supporting interactive provider selection:
    Providers: 'ollama', 'gemini', 'openai', 'router' (heterogeneous multi-agent), 'fallback'.
    """
    def __init__(self, provider_type: str = "fallback", model_name: Optional[str] = None) -> None:
        self.provider_type = provider_type.lower()
        self.router = HeterogeneousRouterLLMClient() if self.provider_type == "router" else None
        self.provider = self._select_provider(self.provider_type, model_name)

    def _select_provider(self, ptype: str, model_name: Optional[str]) -> BaseLLMProvider:
        if ptype == "ollama":
            model = model_name or "qwen2.5-coder:7b"
            return OllamaLocalProvider(model_name=model)
        elif ptype == "gemini":
            model = model_name or "gemini-2.5-pro"
            return GoogleGeminiProvider(model_name=model)
        elif ptype == "openai":
            model = model_name or "gpt-4o"
            return OpenAICompatibleProvider(model_name=model)
        else:
            return FallbackDeterministicProvider()

    def complete(self, prompt: str, system_prompt: Optional[str] = None, agent_name: str = "default") -> str:
        if self.router:
            return self.router.complete_for_agent(agent_name, prompt, system_prompt)

        messages: List[LLMMessage] = []
        if system_prompt:
            messages.append(LLMMessage(role="system", content=system_prompt))
        messages.append(LLMMessage(role="user", content=prompt))

        resp = self.provider.generate(messages)
        return resp.content
