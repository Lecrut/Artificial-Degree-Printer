"""Wave 1 of Audit III (§III.9): timeouts as findings, the skeleton task, the interface contract between tasks,
symbol edits and the context of a repair."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from adk.orchestration.common import MaterializationError
from adk.orchestrator import NeuroSymbolicOrchestrator
from adk.tools.building.ast_editor import edit_ast_node
from adk.tools.building.import_sync import extract_hyperedge_exports
from adk.tools.building.hypergraph_sync import sync_hypergraph_matrix
from adk.tools.verification import test_runner


def _orch(tmp_path: Path) -> NeuroSymbolicOrchestrator:
    orch = NeuroSymbolicOrchestrator(adk_root="adk", enable_layer4=False, provider="mock")
    orch.workspace_dir = tmp_path / "workspace"
    orch.state_dir = tmp_path / "state"
    orch.workspace_dir.mkdir(parents=True, exist_ok=True)
    orch.state_dir.mkdir(parents=True, exist_ok=True)
    orch.task_queue_path = orch.state_dir / "task_queue.json"
    orch.validation_report_path = orch.state_dir / "validation_report.json"
    orch.blueprint_path = orch.state_dir / "academic_blueprint.json"
    orch.failure_ledger_path = orch.state_dir / "failure_ledger.json"
    orch.hitl_flag_path = orch.state_dir / "hitl_flag.json"
    orch.evolution_history_path = orch.state_dir / "evolution_history.json"
    orch.matrix_path = orch.state_dir / "hypergraph_matrix.json"
    shutil.copy2(Path("adk") / "state" / "hypergraph_matrix.json", orch.matrix_path)
    return orch


SKELETON_AGENT = (
    "class Agent:\n"
    "    def __init__(self, alpha: float) -> None:\n"
    "        raise NotImplementedError\n\n"
    "    def act(self, state: tuple) -> int:\n"
    "        \"\"\"Returns the chosen action index.\"\"\"\n"
    "        raise NotImplementedError\n"
)


def test_hung_test_is_a_finding_naming_the_test_not_an_exception(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression (2026-11-12): a generated test looped forever, TimeoutExpired escaped and ended the run."""
    monkeypatch.setattr(test_runner, "PER_TEST_TIMEOUT_S", 2)
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "loop.py").write_text("def spin() -> None:\n    while True:\n        pass\n", encoding="utf-8")
    (ws / "test_loop.py").write_text("from loop import spin\n\n\ndef test_spin() -> None:\n    spin()\n", encoding="utf-8")

    res = test_runner.run_isolated_tests(ws, verification_dir=tmp_path / "no_validators")

    assert res["status"] == "FAIL"
    hang = next(e for e in res["errors"] if e.startswith("Pytest failure"))
    assert "zawiesił się" in hang and "test_loop.py" in hang and "loop.py" in hang


def test_exports_carry_class_method_signatures(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    (orch.workspace_dir / "agent.py").write_text(SKELETON_AGENT, encoding="utf-8")
    sync_hypergraph_matrix(orch.workspace_dir, orch.matrix_path)

    exports = extract_hyperedge_exports("ALL", orch.matrix_path, orch.workspace_dir)["exports"]["agent.py"]

    assert exports["signatures"]["Agent.__init__"] == "def __init__(self, alpha: float) -> None"
    assert exports["signatures"]["Agent.act"] == "def act(self, state: tuple) -> int"


def test_symbol_edit_replaces_one_method_inside_its_class(tmp_path: Path) -> None:
    path = tmp_path / "agent.py"
    path.write_text(SKELETON_AGENT, encoding="utf-8")

    res = edit_ast_node(path, "Agent.act", "def act(self, state: tuple) -> int:\n    return 0\n")

    assert res["status"] == "ok" and res["action"] == "replaced"
    source = path.read_text(encoding="utf-8")
    assert "return 0" in source and source.count("def act") == 1 and "def __init__" in source
    assert edit_ast_node(path, "Missing.act", "def act(self) -> int:\n    return 1\n")["status"] == "error"


def _establish(orch: NeuroSymbolicOrchestrator) -> None:
    orch._materialize_workspace_artifact(
        "agent.py",
        {"files": [{"filename": "agent.py", "content": SKELETON_AGENT}, {"filename": "test_agent.py", "content": "x = 1\n"}]},
        establishes_contract=True,
    )


def test_skeleton_establishes_the_contract_of_code_modules_only(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    _establish(orch)

    contract = json.loads(orch.interface_contract_path.read_text(encoding="utf-8"))

    assert contract == {"agent.py": {"Agent": [], "Agent.__init__": ["self", "alpha"], "Agent.act": ["self", "state"]}}


def test_unexplained_signature_change_is_rejected_and_the_file_restored(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    _establish(orch)
    drifted = SKELETON_AGENT.replace("def act(self, state: tuple)", "def get_action(self, state: tuple, valid: list)")

    with pytest.raises(MaterializationError, match="Agent.act"):
        orch._materialize_workspace_artifact("agent.py", {"files": [{"filename": "agent.py", "content": drifted}]})

    assert (orch.workspace_dir / "agent.py").read_text(encoding="utf-8") == SKELETON_AGENT


def test_named_contract_change_is_accepted_and_recorded(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    _establish(orch)
    changed = SKELETON_AGENT.replace("def act(self, state: tuple)", "def act(self, state: tuple, valid: list)")

    orch._materialize_workspace_artifact(
        "agent.py",
        {"files": [{"filename": "agent.py", "content": changed}], "contract_change": {"reason": "akcje legalne z planszy"}},
    )

    contract = json.loads(orch.interface_contract_path.read_text(encoding="utf-8"))
    assert contract["agent.py"]["Agent.act"] == ["self", "state", "valid"]
    events = json.loads(orch.evolution_history_path.read_text(encoding="utf-8"))["events"]
    assert any(e["type"] == "CONTRACT_CHANGED" and e["reason"] == "akcje legalne z planszy" for e in events)


def test_filling_in_bodies_and_adding_symbols_is_free(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    _establish(orch)

    orch._materialize_workspace_artifact(
        "agent.py",
        {
            "ast_edits": [
                {"symbol": "Agent.act", "file": "agent.py", "code": "def act(self, state: tuple) -> int:\n    return 0\n"},
                {"symbol": "Agent.reset", "file": "agent.py", "code": "def reset(self) -> None:\n    return None\n"},
            ]
        },
    )

    contract = json.loads(orch.interface_contract_path.read_text(encoding="utf-8"))
    assert "Agent.reset" in contract["agent.py"] and "return 0" in (orch.workspace_dir / "agent.py").read_text(encoding="utf-8")


def test_rejected_symbol_edit_is_an_error_and_nothing_of_the_answer_is_written(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    _establish(orch)

    with pytest.raises(MaterializationError, match="Edycje symboli odrzucone"):
        orch._materialize_workspace_artifact(
            "agent.py",
            {
                "files": [{"filename": "helper.py", "content": "VALUE = 1\n"}],
                "ast_edits": [{"symbol": "Agent.act", "file": "agent.py", "code": "def act(self, state:\n"}],
            },
        )

    assert not (orch.workspace_dir / "helper.py").exists()
    assert (orch.workspace_dir / "agent.py").read_text(encoding="utf-8") == SKELETON_AGENT


def test_healing_puts_a_skeleton_of_all_modules_before_the_first_code_task(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    orch.blueprint_path.write_text(json.dumps({"entrypoint": "run.py:main"}), encoding="utf-8")
    planned = [
        {"task_id": "T1", "description": "Literatura", "target_node": "thesis.md", "assigned_agent": "background_researcher"},
        {"task_id": "T2", "description": "Środowisko", "target_node": "env.py", "assigned_agent": "seed_coder"},
        {"task_id": "T3", "description": "Agent", "target_node": "agent.py", "assigned_agent": "seed_coder"},
        {"task_id": "T4", "description": "Testy agenta", "target_node": "test_agent.py", "assigned_agent": "seed_tester"},
        {"task_id": "T5", "description": "Eksperyment", "target_node": "run.py", "assigned_agent": "seed_coder"},
    ]

    healed = orch._normalize_and_heal_task_plan(planned, user_prompt="RL", multi_cycle_waves=True)
    ids = [t["task_id"] for t in healed]

    skeleton = next(t for t in healed if t["task_id"] == "SKELETON")
    assert ids.index("SKELETON") == ids.index("T2") - 1
    assert all(m in skeleton["description"] for m in ("env.py", "agent.py", "run.py"))
    assert "test_agent.py" not in skeleton["description"]


def test_planner_skeleton_task_is_kept_and_moved_before_the_code(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    planned = [
        {"task_id": "T1", "description": "Środowisko", "target_node": "env.py", "assigned_agent": "seed_coder"},
        {"task_id": "T2", "description": "Agent", "target_node": "agent.py", "assigned_agent": "seed_coder"},
        {"task_id": "T3", "description": "Szkielet modułów projektu", "target_node": "env.py", "assigned_agent": "seed_coder"},
    ]

    healed = orch._normalize_and_heal_task_plan(planned, user_prompt="RL", multi_cycle_waves=True)

    descriptions = [t["description"] for t in healed]  # healing renumbers task ids, descriptions stay
    skeleton_at = next(i for i, t in enumerate(healed) if t["task_id"] == "SKELETON")
    assert healed[skeleton_at]["description"].startswith("Szkielet modułów projektu")
    assert skeleton_at < descriptions.index("Środowisko") < descriptions.index("Agent")
    assert sum(1 for d in descriptions if "zkielet" in d) == 1


def test_repair_payload_carries_the_source_of_the_failing_tests(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    (orch.workspace_dir / "test_agent.py").write_text(
        "class TestAgent:\n    def test_act(self) -> None:\n        assert 1 == 2\n\n\ndef test_other() -> None:\n    pass\n",
        encoding="utf-8",
    )
    report = {
        "status": "FAIL",
        "supervisors": {
            "code_auditor": {
                "issues": ["Pytest failure: F.\nFAILED test_agent.py::TestAgent::test_act - assert 1 == 2\n1 failed, 1 passed"]
            }
        },
    }
    orch.validation_report_path.write_text(json.dumps(report), encoding="utf-8")

    failing = orch._failing_test_sources()

    assert list(failing) == ["test_agent.py::TestAgent::test_act"]
    assert failing["test_agent.py::TestAgent::test_act"]["error"] == "assert 1 == 2"
    assert "def test_act" in failing["test_agent.py::TestAgent::test_act"]["source"]


def test_crashed_orchestrator_still_gives_the_run_a_status(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from adk.benchmarks import run_benchmark_suite
    from unittest.mock import MagicMock

    from adk.benchmarks import runner

    monkeypatch.setattr(runner.NeuroSymbolicOrchestrator, "run", MagicMock(side_effect=RuntimeError("narzędzie padło")))
    res = run_benchmark_suite(task_keys=["2"], provider="mock", output_root=tmp_path / "out")

    assert res["tasks"][0]["orchestrator_status"] == "CRASHED"
    assert "narzędzie padło" in res["tasks"][0]["orchestrator_error"]
