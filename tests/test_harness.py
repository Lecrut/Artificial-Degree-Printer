from adk.tool_registry import ToolRegistry, ToolSpec
from adk.workflow import PipelineStage, TaskGraph


def test_task_graph_keeps_ordered_stages():
    graph = TaskGraph()
    graph.add_stage(PipelineStage("intake", "Collect requirements"))
    graph.add_stage(PipelineStage("plan", "Build the execution plan"))
    graph.add_stage(PipelineStage("verify", "Validate results"))

    assert [stage.name for stage in graph.stages] == ["intake", "plan", "verify"]


def test_tool_registry_registers_and_lists_tools():
    registry = ToolRegistry()
    registry.register(ToolSpec("filesystem", "Read and write files"))
    registry.register(ToolSpec("terminal", "Run shell commands"))

    assert registry.has("filesystem") is True
    assert registry.has("terminal") is True
    assert registry.get("filesystem").description == "Read and write files"
    assert registry.list_names() == ["filesystem", "terminal"]


def test_detect_task_type_handles_common_it_work():
    from adk.task_types import detect_task_type

    assert detect_task_type("Build a FastAPI backend service with database models") == "backend"
    assert detect_task_type("Create a React dashboard for analytics") == "frontend"
    assert detect_task_type("Fix a production bug in login flow") == "bugfix"
    assert detect_task_type("Set up a deployment pipeline for AWS") == "devops"
    assert detect_task_type("Write technical documentation for the API") == "documentation"


def test_harness_supports_generic_task_and_agent_registration():
    from adk.harness import AgentHarness

    harness = AgentHarness()
    harness.register_agent("architect", "Designs the system")
    harness.register_agent("verifier", "Runs validation")
    harness.register_task_type("backend", "Server and API work", ["api", "service", "database"])

    assert harness.task_graph.get_stage("architect").description == "Designs the system"
    assert harness.task_graph.get_stage("verifier").description == "Runs validation"
    assert harness.task_registry.get("backend").description == "Server and API work"


def test_default_workflow_builds_execution_order_for_it_tasks():
    from adk.harness import AgentHarness

    harness = AgentHarness()
    workflow = harness.build_default_workflow("backend")

    assert [stage.name for stage in workflow.stages] == [
        "intake",
        "research",
        "planning",
        "implementation",
        "verification",
        "delivery",
    ]


def test_task_graph_rejects_cycles_and_missing_dependencies():
    from adk.workflow import PipelineStage, TaskGraph

    graph = TaskGraph()
    graph.add_stage(PipelineStage("intake", "Collect requirements", []))
    graph.add_stage(PipelineStage("planning", "Plan the work", ["implementation"]))
    graph.add_stage(PipelineStage("implementation", "Build the solution", ["planning"]))

    assert graph.has_cycle() is True
    assert graph.find_missing_dependencies() == {"planning": ["implementation"], "implementation": ["planning"]}
