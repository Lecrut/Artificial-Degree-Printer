"""Fixes from the 2026-11-15 run of benchmark 01 (Audit V §VI.11: N2, N3, N4, N6, N7)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from adk.orchestration.common import MaterializationError, _issue_category
from adk.orchestrator import NeuroSymbolicOrchestrator
from adk.tools.verification.contract_check import interface_contract_breaches, interface_contract_extensions


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


def _events(orch: NeuroSymbolicOrchestrator) -> list[dict]:
    return json.loads(orch.evolution_history_path.read_text(encoding="utf-8"))["events"]


TEST = "def test_x() -> None:\n    assert True\n"
CODER = {"agent": "seed_coder", "task_id": "T20_FIX1"}


def test_coder_cannot_rewrite_a_test_but_keeps_the_rest_of_its_answer(tmp_path: Path) -> None:
    """N2: the coder fixed failed assertions by rewriting the test (7x CROSS_ROLE_WRITE)."""
    orch = _orch(tmp_path)
    (orch.workspace_dir / "test_experiment.py").write_text(TEST, encoding="utf-8")

    orch._materialize_workspace_artifact(
        "experiment.py",
        {"files": [
            {"filename": "experiment.py", "content": "X = 1\n"},
            {"filename": "test_experiment.py", "content": "def test_x() -> None:\n    pass\n"},
        ]},
        writer=CODER,
    )

    assert (orch.workspace_dir / "experiment.py").read_text(encoding="utf-8") == "X = 1\n"
    assert (orch.workspace_dir / "test_experiment.py").read_text(encoding="utf-8") == TEST
    assert any(e["type"] == "CODER_TEST_WRITE_SKIPPED" for e in _events(orch))


def test_coder_answer_that_only_touches_a_test_is_refused_with_the_reason(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    (orch.workspace_dir / "test_experiment.py").write_text(TEST, encoding="utf-8")

    with pytest.raises(MaterializationError, match="belong to the tester"):
        orch._materialize_workspace_artifact(
            "experiment.py",
            {"ast_edits": [{"symbol": "test_x", "file": "test_experiment.py", "code": "def test_x() -> None:\n    pass\n"}]},
            writer=CODER,
        )
    assert (orch.workspace_dir / "test_experiment.py").read_text(encoding="utf-8") == TEST


def test_tester_still_writes_tests(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    orch._materialize_workspace_artifact(
        "test_env.py", {"files": [{"filename": "test_env.py", "content": TEST}]},
        writer={"agent": "seed_tester", "task_id": "T9"},
    )
    assert (orch.workspace_dir / "test_env.py").exists()


def test_workspace_prefix_is_stripped_and_a_test_lands_in_its_existing_file(tmp_path: Path) -> None:
    """N3: `workspace/tests/test_experiment.py` created a nested workspace/ and duplicate tests appeared."""
    orch = _orch(tmp_path)
    (orch.workspace_dir / "tests").mkdir()
    (orch.workspace_dir / "tests" / "test_experiment.py").write_text(TEST, encoding="utf-8")
    new = "def test_y() -> None:\n    assert True\n"

    orch._materialize_workspace_artifact(
        "tests/test_experiment.py",
        {"files": [
            {"filename": "workspace/src/run.py", "content": "Y = 2\n"},
            {"filename": "test_experiment.py", "content": new},
        ]},
        writer={"agent": "seed_tester", "task_id": "T21"},
    )

    assert (orch.workspace_dir / "src" / "run.py").exists()
    assert not (orch.workspace_dir / "workspace").exists()
    assert (orch.workspace_dir / "tests" / "test_experiment.py").read_text(encoding="utf-8") == new
    assert not (orch.workspace_dir / "test_experiment.py").exists()


def test_category_uses_the_full_exception_name_not_the_truncated_summary() -> None:
    """N4: the short summary cut names to 'AssertionEr...'; one failure became several categories."""
    truncated = (
        "Pytest failure: F\n___ test_run ___\ntest_e.py:3: in test_run\n    assert f()\n"
        "E   AssertionError: no results\nFAILED test_e.py::test_run - AssertionEr...\n"
    )
    assert _issue_category([truncated]) == "pytest:AssertionError"


def test_first_parameters_of_a_placeholder_signature_are_allowed_and_recorded() -> None:
    """N6: `Config.__init__(self)` -> `Config.__init__(self, learning_rate, ...)` was rejected 9 times."""
    contract = {"config.py": {"Config": [], "Config.__init__": ["self"], "Config.to_dict": ["self"]}}
    filled = (
        "class Config:\n"
        "    def __init__(self, learning_rate: float, gamma: float) -> None:\n        self.lr = learning_rate\n\n"
        "    def to_dict(self) -> dict:\n        return {}\n"
    )
    assert interface_contract_breaches(contract, "config.py", filled) == []
    assert interface_contract_extensions(contract, "config.py", filled) == [
        "config.py: Config.__init__(self) -> Config.__init__(self, learning_rate, gamma)"
    ]
    changed = filled.replace("learning_rate: float, gamma: float", "gamma: float")
    contract_real = {"config.py": {"Config.__init__": ["self", "learning_rate", "gamma"]}}
    assert interface_contract_breaches(contract_real, "config.py", changed)  # a real signature stays protected


def test_ast_edits_on_a_document_and_malformed_elements_get_a_clear_reason(tmp_path: Path) -> None:
    """N7: ast_edits on thesis.md answered 'SyntaxError in new_code'; a malformed element vanished."""
    orch = _orch(tmp_path)
    (orch.workspace_dir / "thesis.md").write_text("# Praca\n", encoding="utf-8")

    with pytest.raises(MaterializationError, match=r"only for \.py files.*'sections'"):
        orch._materialize_workspace_artifact(
            "thesis.md", {"ast_edits": [{"symbol": "LastSection", "file": "thesis.md", "code": "## X\ntekst\n"}]}
        )
    with pytest.raises(MaterializationError, match=r"without the required 'symbol' or 'code'.*\['content', 'name'\]"):
        orch._materialize_workspace_artifact("a.py", {"ast_edits": [{"name": "f", "content": "def f(): pass"}]})


def test_task_echoed_back_in_the_answer_is_ignored(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    orch._materialize_workspace_artifact(
        "a.py", {"task": {"task_id": "T1"}, "files": [{"filename": "a.py", "content": "A = 1\n"}]}
    )
    assert (orch.workspace_dir / "a.py").exists()
