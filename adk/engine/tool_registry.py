from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ToolSpec:
    name: str
    description: str
    capabilities: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        self.description = self.description.strip()
        if not self.name:
            raise ValueError("Tool name cannot be empty.")


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, tool: ToolSpec) -> ToolSpec:
        self._tools[tool.name] = tool
        return tool

    def get(self, name: str) -> ToolSpec:
        return self._tools[name]

    def has(self, name: str) -> bool:
        return name in self._tools

    def list_names(self) -> list[str]:
        return sorted(self._tools)

