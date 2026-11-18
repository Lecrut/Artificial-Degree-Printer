"""Stage 1 of Audit IV: a task is judged on its own node (R4), blame goes to the file's author (R5), routing
never matches a filename as a substring (R3), and writes across roles / off target are logged (R6)."""

from __future__ import annotations

import json
from pathlib import Path

from adk.orchestrator import NeuroSymbolicOrchestrator
from adk.tools.verification import test_runner
from adk.tools.verification.contract_check import check_import_contract
from tests._plans import with_plan


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


def _write(ws: Path, rel: str, text: str) -> None:
    (ws / rel).parent.mkdir(parents=True, exist_ok=True)
    (ws / rel).write_text(text, encoding="utf-8")


def test_a_task_passes_despite_a_broken_file_it_does_not_own(tmp_path: Path) -> None:
    """2026-11-13: T7-T9 had correct modules and were FAILED because of three broken siblings."""
    orch = _orch(tmp_path)
    ws = orch.workspace_dir
    _write(ws, "src/__init__.py", "")
    _write(ws, "src/q_learner.py", "class QLearner:\n    def act(self) -> int:\n        return 0\n")
    _write(ws, "src/tictoc_env.py", "def broken(:\n")

    report = orch._run_verification_step(
        {"task_id": "T7", "target_node": "src/q_learner.py", "assigned_agent": "seed_coder"}, include_docs=False
    )

    assert report["status"] == "PASS", report
    assert any("tictoc_env.py" in w and "Outside the task's scope" in w for w in report.get("warnings", []))


def test_import_failure_caused_by_a_sibling_is_not_this_files_error(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    _write(ws, "src/__init__.py", "from . import env\n")
    _write(ws, "src/env.py", "def broken(:\n")
    _write(ws, "src/learner.py", "X = 1\n")

    res = test_runner.run_isolated_tests(ws, verification_dir=tmp_path / "none", scope={"files": ["src/learner.py"], "tests": []})

    assert res["status"] == "PASS", res["errors"]
    assert any("src/env.py" in note for note in res["out_of_scope"])


def test_static_import_contract_catches_a_wrong_name_without_running_anything(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    _write(ws, "src/__init__.py", "")
    _write(ws, "src/game.py", "class TicTacToeGame:\n    pass\n")
    _write(ws, "src/env.py", "from .game import TicTacToe\nfrom src.game import TicTacToeGame\n")

    violations = check_import_contract(ws, "src/env.py")

    assert len(violations) == 1
    assert "TicTacToe " in violations[0] + " " and "TicTacToeGame" in violations[0]


def test_writer_task_is_not_judged_on_code(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    ws = orch.workspace_dir
    _write(ws, "core.py", "def broken(:\n")
    _write(ws, "thesis.md", "# Wstęp\nTekst bez wskaźników.\n")

    report = orch._run_verification_step(
        {"task_id": "T15", "target_node": "thesis.md", "assigned_agent": "seed_writer"}, include_docs=True
    )

    assert report["status"] == "PASS", report


def _game_with_test(tmp_path: Path, test_body: str) -> NeuroSymbolicOrchestrator:
    """game.py (coder) and its test (tester), as planned: the test is a T member of game.py's I bag in H."""
    orch = _orch(tmp_path)
    with_plan(
        orch, {"game.py": '"""Game."""\n\n\ndef size() -> int:\n    """Board size."""\n'}, None,
        [{"task_id": "T10", "target_node": "tests/test_game.py", "description": "tests", "assigned_agent": "seed_tester"}],
    )
    orch._materialize_workspace_artifact(
        "game.py", {"files": [{"filename": "game.py", "content": '"""Game."""\n\n\ndef size() -> int:\n    """Board size."""\n    return 9\n'}]},
        writer={"agent": "seed_coder", "task_id": "T5"},
    )
    orch._materialize_workspace_artifact(
        "tests/test_game.py",
        {"files": [{"filename": "tests/test_game.py", "content": "from game import size\n\n\ndef test_size() -> None:\n" + test_body}]},
        writer={"agent": "seed_tester", "task_id": "T10"},
    )
    return orch


def test_a_wrong_result_goes_to_the_author_of_the_code_under_test(tmp_path: Path) -> None:
    """2026-11-14: a failed assertion was charged to the test file (named first by pytest); 77 repairs went to
    the tester while the bug was in the module. The module under test is read from H (the test's I bag)."""
    orch = _game_with_test(tmp_path, "    assert size() == 10\n")

    report = orch._run_verification_step(
        {"task_id": "T10", "target_node": "tests/test_game.py", "assigned_agent": "seed_tester"}, include_docs=False
    )

    assert report["status"] == "FAIL"
    assert report["failed_file"] == "game.py"
    assert report["failed_agent"] == "seed_coder"


def test_a_test_misusing_the_api_is_returned_to_the_tester_at_once(tmp_path: Path) -> None:
    """A test that calls the planned API wrongly never reaches the coder's verification: run on the stubs it fails
    for a reason of its own, and the write goes back to the tester (Φ_I.4)."""
    import pytest

    from adk.orchestration.common import MaterializationError

    with pytest.raises(MaterializationError, match="TEST_INVALID_ON_STUBS"):
        _game_with_test(tmp_path, "    assert size(3) == 9\n")


def test_explicit_path_never_routes_to_a_file_whose_name_merely_contains_it(tmp_path: Path) -> None:
    """2026-11-13: T4 on `tictoc_config.py` was sent to `config.py` by a substring match in the description."""
    import pytest

    orch = _orch(tmp_path)
    with_plan(orch, {"config.py": '"""Config."""\nSEED: int = 1\n'})

    assert orch._resolve_target_node(
        "tictoc_config.py", task={"description": "Moduł konfiguracji `tictoc_config.py` z klasą Config"}
    ) == ("tictoc_config.py", "tictoc_config.py")
    # A label that is not a path, whose description names no planned file: an error, never `config.py`.
    with pytest.raises(ValueError):
        orch._resolve_target_node("v9", task={"description": "Uzupełnij tictoc_config.py."})


def test_cross_role_writes_are_logged(tmp_path: Path) -> None:
    """A tester writing a module is logged (R6). A coder writing a test is skipped outright (N2, 2026-11-15;
    see tests/test_run_1115_fixes.py)."""
    orch = _orch(tmp_path)
    orch._materialize_workspace_artifact(
        "test_game.py",
        {"files": [
            {"filename": "test_game.py", "content": "def test_x() -> None:\n    pass\n"},
            {"filename": "game.py", "content": "X = 1\n"},
        ]},
        writer={"agent": "seed_tester", "task_id": "T10"},
    )

    events = json.loads(orch.evolution_history_path.read_text(encoding="utf-8"))["events"]
    kinds = {e["type"]: e for e in events}
    assert kinds["CROSS_ROLE_WRITE"]["files"] == ["game.py"]
