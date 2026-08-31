from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class AgentSpec:
    name: str
    description: str
    capabilities: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        self.description = self.description.strip()
        if not self.name:
            raise ValueError("Agent name cannot be empty.")


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, AgentSpec] = {}

    def register(self, agent: AgentSpec) -> AgentSpec:
        self._agents[agent.name] = agent
        return agent

    def get(self, name: str) -> AgentSpec:
        return self._agents[name]

    def has(self, name: str) -> bool:
        return name in self._agents

    def list_names(self) -> list[str]:
        return sorted(self._agents)

