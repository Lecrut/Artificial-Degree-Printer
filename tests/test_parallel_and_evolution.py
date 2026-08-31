import pytest
import time
from pathlib import Path

from adk.core.models import ThesisMetadata
from adk.core.state import ADKProjectState
from adk.engine.graph import StateGraphEngine
from adk.engine.harness import CrystallizedWorkflowRegistry, SelfEvolvingHarnessEngine


from adk.core.events import EventType


def test_state_graph_execute_parallel() -> None:
    engine = StateGraphEngine()
    
    # Create an initial state
    meta = ThesisMetadata(title="Parallel Execution Benchmark Test", student_name="Student", advisor_name="Advisor")
    state = ADKProjectState(metadata=meta)
    
    # Step 1: Intake (Root)
    def intake_action(s: ADKProjectState) -> ADKProjectState:
        s.record_event(event_type=EventType.STAGE_COMPLETED, stage_name="intake", agent_name="orchestrator", payload={"status": "ok"})
        return s

    # Step 2A: Python Code Generation (Depends on Intake)
    def dev_action(s: ADKProjectState) -> ADKProjectState:
        time.sleep(0.05)  # Simulate work
        s.record_event(event_type=EventType.STAGE_COMPLETED, stage_name="developer", agent_name="developer", payload={"code": "done"})
        return s

    # Step 2B: Typst Layout Preparation (Depends on Intake — Independent of 2A!)
    def typeset_action(s: ADKProjectState) -> ADKProjectState:
        time.sleep(0.05)  # Simulate work
        s.record_event(event_type=EventType.STAGE_COMPLETED, stage_name="typesetter", agent_name="typesetter", payload={"typst": "done"})
        return s

    # Step 3: Verification (Depends on 2A and 2B)
    def verify_action(s: ADKProjectState) -> ADKProjectState:
        s.record_event(event_type=EventType.STAGE_COMPLETED, stage_name="verification", agent_name="reviewer", payload={"verified": True})
        return s

    engine.add_node(name="intake", description="Intake", action=intake_action)
    engine.add_node(name="developer", description="Dev", action=dev_action, depends_on=["intake"])
    engine.add_node(name="typesetter", description="Typeset", action=typeset_action, depends_on=["intake"])
    engine.add_node(name="verification", description="Verify", action=verify_action, depends_on=["developer", "typesetter"])

    final_state = engine.execute_parallel(state, max_workers=2)

    # Check that events from all nodes exist
    stages_executed = [e.stage_name for e in final_state.events if e.event_type == EventType.STAGE_COMPLETED]
    assert "intake" in stages_executed
    assert "developer" in stages_executed
    assert "typesetter" in stages_executed
    assert "verification" in stages_executed
    assert engine.parallel_execution_count >= 1


def test_vmao_branch_level_replanning() -> None:
    engine = StateGraphEngine()
    meta = ThesisMetadata(title="Branch Replanning Test", student_name="Student", advisor_name="Advisor")
    state = ADKProjectState(metadata=meta)
    
    execution_counter: dict[str, int] = {"dev": 0, "review": 0}

    def dev_action(s: ADKProjectState) -> ADKProjectState:
        execution_counter["dev"] += 1
        return s

    def review_action(s: ADKProjectState) -> ADKProjectState:
        execution_counter["review"] += 1
        return s

    engine.add_node("developer", "Dev", dev_action)
    engine.add_node("reviewer", "Review", review_action, depends_on=["developer"])

    state = engine.execute_all(state)
    assert execution_counter["dev"] == 1
    assert execution_counter["review"] == 1

    # Isolated branch replan on developer step
    state = engine.replan_branch("developer", state)
    assert execution_counter["dev"] == 2
    assert execution_counter["review"] == 2


def test_tacomas_birth_death_node_swarm() -> None:
    engine = StateGraphEngine()
    meta = ThesisMetadata(title="Swarm Birth Death Test", student_name="Student", advisor_name="Advisor")
    state = ADKProjectState(metadata=meta)

    # Birth node creation
    birth_node = engine.spawn_specialist_node(
        domain_name="quantum_security",
        description="Specialist in Quantum Key Distribution",
        action=lambda s: s,
    )
    assert birth_node.name == "birth_node_quantum_security"
    assert "birth_node_quantum_security" in engine.nodes

    # Execute
    state = engine.execute_all(state)

    # Death node retirement
    retired = engine.retire_node("birth_node_quantum_security")
    assert retired is True
    assert "birth_node_quantum_security" not in engine.nodes


def test_progressive_crystallization_registry(tmp_path: Path) -> None:
    registry = CrystallizedWorkflowRegistry(memory_dir=tmp_path)
    pattern = "typst_header_template"

    assert registry.is_crystallized(pattern) is False

    # Execute 3 times to achieve crystallization threshold
    registry.register_crystallized_pattern(pattern, "deterministic_typst_header()", execution_count=1)
    assert registry.is_crystallized(pattern) is False

    registry.register_crystallized_pattern(pattern, "deterministic_typst_header()", execution_count=3)
    assert registry.is_crystallized(pattern) is True


def test_paste_speculative_tool_execution() -> None:
    engine = StateGraphEngine()
    meta = ThesisMetadata(title="PASTE Speculation Test", student_name="Student", advisor_name="Advisor")
    state = ADKProjectState(metadata=meta)

    speculative_flag: dict[str, bool] = {"executed": False}

    def background_prefetch(s: ADKProjectState) -> ADKProjectState:
        speculative_flag["executed"] = True
        s.record_event(
            event_type=EventType.STAGE_COMPLETED,
            stage_name="prefetch",
            agent_name="paste_speculator",
            payload={"prefetched": True},
        )
        return s

    final_state = engine.execute_speculative_tools(
        current_stage="architecture",
        state=state,
        prefetch_actions=[background_prefetch],
    )

    assert speculative_flag["executed"] is True
    paste_events = [e for e in final_state.events if e.agent_name == "paste_speculator"]
    assert len(paste_events) >= 1

