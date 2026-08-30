import tempfile
from pathlib import Path
import pytest

from adk.core.events import EventType
from adk.core.models import HarnessPatch, VerificationIssue, VerificationReport
from adk.core.state import ADKProjectState
from adk.engine.context import ExecutionContext
from adk.engine.graph import StateGraphEngine
from adk.engine.harness import SelfEvolvingHarnessEngine


def test_harness_engine_create_and_save_patch():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        engine = SelfEvolvingHarnessEngine(memory_dir=tmp_path)
        assert len(engine.registry.patches) == 0

        issue = VerificationIssue(
            stage="implementation",
            severity="ERROR",
            message="AST syntax error in generated code",
            suggested_fix="Use ast.parse to validate before saving",
        )

        patch = engine.create_patch(
            failed_issue=issue,
            agent_name="developer",
            patch_instruction="Always run ast.parse verification before returning code content.",
        )

        assert patch.id.startswith("HP-DEVE-")
        assert patch.target_agent == "developer"
        assert patch.is_active is True

        # Test GSME evaluation gate (Passing report)
        passing_report = VerificationReport(passed=True, score=95.0)
        accepted = engine.evaluate_and_evolve(patch, lambda: passing_report)
        assert accepted is True
        assert len(engine.registry.patches) == 1

        # Test persistence
        saved_file = tmp_path / "harness_repairs.json"
        assert saved_file.exists()

        # Reload in new engine instance
        new_engine = SelfEvolvingHarnessEngine(memory_dir=tmp_path)
        assert len(new_engine.registry.patches) == 1
        assert new_engine.registry.patches[0].id == patch.id


def test_harness_engine_gsme_rejection_gate():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        engine = SelfEvolvingHarnessEngine(memory_dir=tmp_path)

        issue = VerificationIssue(
            stage="typesetting",
            severity="ERROR",
            message="Missing BibTeX key in chapter text",
        )

        patch = engine.create_patch(
            failed_issue=issue,
            agent_name="typesetter",
            patch_instruction="Remove unverified citations.",
        )

        # Test GSME evaluation gate (Failing report) -> Must reject patch to prevent Misevolution
        failing_report = VerificationReport(passed=False, score=40.0)
        accepted = engine.evaluate_and_evolve(patch, lambda: failing_report)
        assert accepted is False
        assert len(engine.registry.patches) == 0


def test_harness_engine_get_relevant_patches():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        engine = SelfEvolvingHarnessEngine(memory_dir=tmp_path)

        patch_dev = HarnessPatch(
            id="HP-001",
            target_agent="developer",
            trigger_condition="AST error",
            patch_instruction="Validate AST",
            verification_gate="CodeVerificationGate",
        )
        patch_all = HarnessPatch(
            id="HP-002",
            target_agent="all",
            trigger_condition="English naming",
            patch_instruction="Check ascii filenames",
            verification_gate="EnglishNamingVerificationGate",
        )

        engine.registry.patches.extend([patch_dev, patch_all])

        dev_patches = engine.get_relevant_patches("developer")
        assert len(dev_patches) == 2

        researcher_patches = engine.get_relevant_patches("researcher")
        assert len(researcher_patches) == 1
        assert researcher_patches[0].id == "HP-002"


def test_execution_context_harness_patches():
    ctx = ExecutionContext()
    patch = HarnessPatch(
        id="HP-TEST",
        target_agent="developer",
        trigger_condition="Test condition",
        patch_instruction="Test instruction",
        verification_gate="TestGate",
    )
    ctx.inject_harness_patches([patch])
    assert "HP-TEST" in ctx.harness_patches
    assert ctx.harness_patches["HP-TEST"].patch_instruction == "Test instruction"


def test_state_graph_with_harness_engine():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        harness_engine = SelfEvolvingHarnessEngine(memory_dir=tmp_path)

        # Pre-seed a patch for developer
        patch = HarnessPatch(
            id="HP-SEED",
            target_agent="developer",
            trigger_condition="AST failure",
            patch_instruction="Enforce AST checks",
            verification_gate="MasterSuite",
        )
        harness_engine.registry.patches.append(patch)

        graph = StateGraphEngine(harness_engine=harness_engine)

        def dummy_action(state: ADKProjectState) -> ADKProjectState:
            state.metadata.title = "Updated Title"
            return state

        graph.add_node("developer", "Develop code", dummy_action)

        initial_state = ADKProjectState()
        final_state = graph.execute_all(initial_state)

        assert final_state.metadata.title == "Updated Title"
        # Check event log recorded harness patch injection
        events = [e for e in final_state.events if e.event_type == EventType.HARNESS_PATCH_INJECTED]
        assert len(events) == 1
        assert events[0].payload["patches_count"] == 1
        assert "HP-SEED" in events[0].payload["patch_ids"]
