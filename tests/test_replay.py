import tempfile
from pathlib import Path

from adk.core.state import ADKProjectState
from adk.engine.replay import TimeTravelReplayEngine


def test_record_step_and_rewind():
    """Verify event recording and state restoration to historical step K."""
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = TimeTravelReplayEngine(memory_dir=Path(tmpdir))

        state1 = ADKProjectState(project_id="p1", request="Step 1 Intake")
        state1.metadata.title = "Krok 1 Title"
        engine.record_step("intake", "OrchestratorAgent", state1, "Initial intake completed")

        state2 = ADKProjectState(project_id="p1", request="Step 2 Architecture")
        state2.metadata.title = "Krok 2 Architecture Title"
        engine.record_step("architecture", "ArchitectAgent", state2, "C4 Architecture generated")

        assert len(engine.events) == 2

        restored = engine.rewind_to_step(1)
        assert restored.metadata.title == "Krok 1 Title"
        assert restored.request == "Step 1 Intake"


def test_branch_timeline():
    """Verify timeline branching creates an independent fork from step K."""
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = TimeTravelReplayEngine(memory_dir=Path(tmpdir))

        state1 = ADKProjectState(project_id="p1", request="Initial Step")
        engine.record_step("intake", "OrchestratorAgent", state1, "Intake step")

        state2 = ADKProjectState(project_id="p1", request="Second Step")
        engine.record_step("research", "ResearcherAgent", state2, "Research step")

        branched_state = engine.branch_timeline(step_index=1, branch_name="duckdb_branch")
        assert branched_state.request == "Initial Step"
        assert "duckdb_branch" in engine.branches
        assert len(engine.branches["duckdb_branch"]) == 1


def test_export_mermaid_timeline():
    """Verify Mermaid timeline diagram generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = TimeTravelReplayEngine(memory_dir=Path(tmpdir))

        state1 = ADKProjectState(project_id="p1", request="Initial Step")
        engine.record_step("intake", "OrchestratorAgent", state1, "Intake step")

        mermaid = engine.export_mermaid_timeline()
        assert "timeline" in mermaid
        assert "INTAKE" in mermaid
        assert "OrchestratorAgent" in mermaid
