from __future__ import annotations

import os
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


class LLMClient:
    def __init__(self, provider: Optional[BaseLLMProvider] = None, model: str = "gemini-2.5-pro") -> None:
        self.model = model
        self.provider = provider or FallbackDeterministicProvider()

    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        messages: List[LLMMessage] = []
        if system_prompt:
            messages.append(LLMMessage(role="system", content=system_prompt))
        messages.append(LLMMessage(role="user", content=prompt))
        
        resp = self.provider.generate(messages)
        return resp.content

