from adk.agents.architect import ArchitectAgent
from adk.agents.developer import DeveloperAgent
from adk.agents.orchestrator import OrchestratorAgent
from adk.agents.researcher import ResearcherAgent
from adk.agents.reviewer import ReviewerAgent
from adk.agents.typesetter import TypesetterAgent
from adk.core.state import ADKProjectState


def test_agent_swarm_execution_flow(tmp_path):
    state = ADKProjectState(project_id="test_swarm", request="System IoT z analizą danych")
    
    orch = OrchestratorAgent()
    state = orch.run(state)
    assert state.metadata.title == "System IoT z analizą danych"
    assert len(state.requirements) > 0

    res = ResearcherAgent()
    state = res.run(state)
    assert len(state.citations) > 0

    arch = ArchitectAgent()
    state = arch.run(state)
    assert state.architecture is not None
    assert len(state.architecture.modules) > 0

    dev = DeveloperAgent()
    state = dev.run(state)
    assert len(state.code_artifacts) > 0

    typ = TypesetterAgent()
    state = typ.run(state)
    assert len(state.chapters) >= 5

    rev = ReviewerAgent()
    state = rev.run(state)
    assert state.verification_report is not None
    assert state.verification_report.score > 70.0

