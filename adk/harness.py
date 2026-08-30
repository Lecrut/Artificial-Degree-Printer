from __future__ import annotations

from dataclasses import dataclass, field

from adk.agent_registry import AgentRegistry, AgentSpec
from adk.task_types import TaskTypeRegistry, TaskTypeSpec
from adk.tool_registry import ToolRegistry, ToolSpec
from adk.workflow import PipelineStage, TaskGraph


DEFAULT_WORKFLOWS: dict[str, list[tuple[str, str, list[str]]]] = {
    "backend": [
        ("intake", "Capture requirements and functional goals", []),
        ("research", "Inspect constraints, architecture, and dependencies", ["intake"]),
        ("planning", "Define API design and implementation plan", ["research"]),
        ("implementation", "Build the service or feature", ["planning"]),
        ("verification", "Run tests and validation checks", ["implementation"]),
        ("delivery", "Prepare final handoff and documentation", ["verification"]),
    ],
    "frontend": [
        ("intake", "Capture product and UI goals", []),
        ("research", "Review UX requirements and components", ["intake"]),
        ("planning", "Design interface and data flow", ["research"]),
        ("implementation", "Build UI and interaction logic", ["planning"]),
        ("verification", "Check accessibility and behavior", ["implementation"]),
        ("delivery", "Prepare handoff and demo notes", ["verification"]),
    ],
    "bugfix": [
        ("intake", "Describe the failure and expected behavior", []),
        ("research", "Reproduce the issue and inspect root cause", ["intake"]),
        ("planning", "Define the smallest fix and validation path", ["research"]),
        ("implementation", "Patch the defect", ["planning"]),
        ("verification", "Validate with focused checks", ["implementation"]),
        ("delivery", "Document the fix and rollback notes", ["verification"]),
    ],
    "devops": [
        ("intake", "Collect deployment and infrastructure requirements", []),
        ("research", "Review environment and constraints", ["intake"]),
        ("planning", "Design CI/CD and infrastructure flow", ["research"]),
        ("implementation", "Configure deployment assets and scripts", ["planning"]),
        ("verification", "Run environment validation and checks", ["implementation"]),
        ("delivery", "Prepare release notes and tracking", ["verification"]),
    ],
    "documentation": [
        ("intake", "Capture audience and project scope", []),
        ("research", "Gather architecture and requirements", ["intake"]),
        ("planning", "Organize structure and key sections", ["research"]),
        ("implementation", "Draft documentation", ["planning"]),
        ("verification", "Check completeness and consistency", ["implementation"]),
        ("delivery", "Publish final documentation package", ["verification"]),
    ],
}


@dataclass(slots=True)
class AgentHarness:
    task_graph: TaskGraph = field(default_factory=TaskGraph)
    tool_registry: ToolRegistry = field(default_factory=ToolRegistry)
    agent_registry: AgentRegistry = field(default_factory=AgentRegistry)
    task_registry: TaskTypeRegistry = field(default_factory=TaskTypeRegistry)

    def register_tool(self, name: str, description: str, capabilities: list[str] | None = None) -> ToolSpec:
        tool = ToolSpec(name=name, description=description, capabilities=capabilities or [])
        return self.tool_registry.register(tool)

    def register_agent(self, name: str, description: str, capabilities: list[str] | None = None) -> AgentSpec:
        agent = AgentSpec(name=name, description=description, capabilities=capabilities or [])
        self.task_graph.add_stage(self._build_stage_from_agent(agent))
        return self.agent_registry.register(agent)

    def register_task_type(self, name: str, description: str, keywords: list[str] | None = None) -> TaskTypeSpec:
        task_type = TaskTypeSpec(name=name, description=description, keywords=keywords or [])
        return self.task_registry.register(task_type)

    def add_stage(self, name: str, description: str, depends_on: list[str] | None = None) -> None:
        stage = PipelineStage(name=name, description=description, depends_on=depends_on or [])
        self.task_graph.add_stage(stage)

    def build_default_workflow(self, task_kind: str) -> TaskGraph:
        workflow = TaskGraph()
        stage_templates = DEFAULT_WORKFLOWS.get(task_kind.lower(), DEFAULT_WORKFLOWS["backend"])

        for name, description, depends_on in stage_templates:
            workflow.add_stage(PipelineStage(name=name, description=description, depends_on=depends_on))

        return workflow

    def _build_stage_from_agent(self, agent: AgentSpec):
        return PipelineStage(name=agent.name, description=agent.description, depends_on=[])
