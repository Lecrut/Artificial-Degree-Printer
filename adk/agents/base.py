from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from adk.core.events import EventType
from adk.core.state import ADKProjectState
from adk.tools.base import BaseTool, ToolResult


class BaseAgent(ABC):
    name: str
    role_description: str
    capabilities: List[str] = []

    def __init__(self, tools: Optional[Dict[str, BaseTool]] = None) -> None:
        self.tools = tools or {}

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        return self.tools.get(tool_name)

    def invoke_tool(self, tool_name: str, **kwargs: Any) -> ToolResult:
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(success=False, error=f"Narzędzie '{tool_name}' nie jest dostępne dla agenta {self.name}.")
        return tool.execute(**kwargs)

    @abstractmethod
    def run(self, state: ADKProjectState, **kwargs: Any) -> ADKProjectState:
        """Wykonuje dedykowaną część pracy w ramach etapu pipeline'u."""
        raise NotImplementedError

