from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class PipelineStage:
    name: str
    description: str
    depends_on: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        self.description = self.description.strip()
        if not self.name:
            raise ValueError("Stage name cannot be empty.")


@dataclass(slots=True)
class TaskGraph:
    stages: list[PipelineStage] = field(default_factory=list)

    def add_stage(self, stage: PipelineStage) -> PipelineStage:
        self.stages.append(stage)
        return stage

    def get_stage(self, name: str) -> PipelineStage | None:
        for stage in self.stages:
            if stage.name == name:
                return stage
        return None

    def stage_names(self) -> list[str]:
        return [stage.name for stage in self.stages]

    def has_cycle(self) -> bool:
        graph: dict[str, list[str]] = {stage.name: stage.depends_on for stage in self.stages}
        visiting: set[str] = set()
        visited: set[str] = set()

        def dfs(node: str) -> bool:
            if node in visiting:
                return True
            if node in visited:
                return False
            visiting.add(node)
            for dependency in graph.get(node, []):
                if dependency not in graph:
                    continue
                if dfs(dependency):
                    return True
            visiting.remove(node)
            visited.add(node)
            return False

        for stage_name in graph:
            if dfs(stage_name):
                return True
        return False

    def find_missing_dependencies(self) -> dict[str, list[str]]:
        stage_map = {stage.name: stage for stage in self.stages}
        graph = {stage.name: stage.depends_on for stage in self.stages}
        missing: dict[str, list[str]] = {}

        for stage in self.stages:
            unresolved: list[str] = []
            for dependency in stage.depends_on:
                if dependency not in stage_map:
                    unresolved.append(dependency)
                    continue
                if self._reaches_cycle(stage.name, dependency, graph):
                    unresolved.append(dependency)
            if unresolved:
                missing[stage.name] = unresolved

        return missing

    def _reaches_cycle(self, start: str, dependency: str, graph: dict[str, list[str]]) -> bool:
        visited: set[str] = set()
        stack: list[str] = [dependency]

        while stack:
            node = stack.pop()
            if node == start:
                return True
            if node in visited:
                continue
            visited.add(node)
            stack.extend(graph.get(node, []))

        return False
