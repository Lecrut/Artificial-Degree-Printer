"""Wave 1 of Audit III (§III.9): timeouts as findings, symbol edits and the context of a repair. (The skeleton task
and the snapshot interface contract were replaced by σ in the project hypergraph: tests/test_audit_vi.py.)"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adk.orchestration.common import MaterializationError
from adk.orchestrator import NeuroSymbolicOrchestrator
from adk.tools.building.ast_editor import edit_ast_node
from adk.hypergraph import spec_from_stub
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
    assert "a test hung" in hang and "test_loop.py" in hang and "loop.py" in hang


def test_specification_carries_class_method_signatures() -> None:
    """What a tester sees of a module is its σ in H: every method with its parameters (2026-11-12: guessed APIs)."""
    symbols = spec_from_stub("agent.py", SKELETON_AGENT, {})["symbols"]

    assert symbols["Agent.__init__"]["params"] == ["self", "alpha"]
    assert symbols["Agent.act"] == {"kind": "method", "params": ["self", "state"], "required": ["state"]}


def test_symbol_edit_replaces_one_method_inside_its_class(tmp_path: Path) -> None:
    path = tmp_path / "agent.py"
    path.write_text(SKELETON_AGENT, encoding="utf-8")

    res = edit_ast_node(path, "Agent.act", "def act(self, state: tuple) -> int:\n    return 0\n")

    assert res["status"] == "ok" and res["action"] == "replaced"
    source = path.read_text(encoding="utf-8")
    assert "return 0" in source and source.count("def act") == 1 and "def __init__" in source
    assert edit_ast_node(path, "Missing.act", "def act(self) -> int:\n    return 1\n")["status"] == "error"


def _establish(orch: NeuroSymbolicOrchestrator) -> None:
    orch._materialize_workspace_artifact("agent.py", {"files": [{"filename": "agent.py", "content": SKELETON_AGENT}]})


def test_rejected_symbol_edit_is_an_error_and_nothing_of_the_answer_is_written(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    _establish(orch)

    with pytest.raises(MaterializationError, match="Symbol edits rejected"):
        orch._materialize_workspace_artifact(
            "agent.py",
            {
                "files": [{"filename": "helper.py", "content": "VALUE = 1\n"}],
                "ast_edits": [{"symbol": "Agent.act", "file": "agent.py", "code": "def act(self, state:\n"}],
            },
        )

    assert not (orch.workspace_dir / "helper.py").exists()
    assert (orch.workspace_dir / "agent.py").read_text(encoding="utf-8") == SKELETON_AGENT


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
