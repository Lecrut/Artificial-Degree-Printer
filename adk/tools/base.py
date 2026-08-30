from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    success: bool = Field(..., description="Czy wykonanie narzędzia zakończyło się sukcesem")
    output: Any = Field(default="", description="Wynik działania narzędzia")
    error: Optional[str] = Field(None, description="Komunikat o błędzie")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Dodatkowe metadane")


class BaseTool(ABC):
    name: str
    description: str
    input_schema: Dict[str, Any] = {}

    @abstractmethod
    def execute(self, **kwargs: Any) -> ToolResult:
        """Wykonuje działanie narzędzia."""
        raise NotImplementedError

