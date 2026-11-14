"""Stage 1 of Audit IV: a task is judged on its own node (R4), blame goes to the file's author (R5), routing
never matches a filename as a substring (R3), and writes across roles / off target are logged (R6)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from adk.orchestrator import NeuroSymbolicOrchestrator
from adk.tools.building.hypergraph_sync import sync_hypergraph_matrix
from adk.tools.verification import test_runner
from adk.tools.verification.contract_check import check_import_contract


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
    sync_hypergraph_matrix(ws, orch.matrix_path)

    report = orch._run_verification_step(
        {"task_id": "T7", "target_node": "src/q_learner.py", "assigned_agent": "seed_coder"}, include_docs=False
    )

    assert report["status"] == "PASS", report
    assert any("tictoc_env.py" in w and "Poza zakresem" in w for w in report.get("warnings", []))


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
    sync_hypergraph_matrix(ws, orch.matrix_path)

    report = orch._run_verification_step(
        {"task_id": "T15", "target_node": "thesis.md", "assigned_agent": "seed_writer"}, include_docs=True
    )

    assert report["status"] == "PASS", report


def test_blame_goes_to_the_author_of_the_failing_file(tmp_path: Path) -> None:
    """A coder's task fails on a test the tester wrote: the tester is the failed agent (R5)."""
    orch = _orch(tmp_path)
    ws = orch.workspace_dir
    orch._materialize_workspace_artifact(
        "game.py", {"files": [{"filename": "game.py", "content": "def size() -> int:\n    return 9\n"}]},
        writer={"agent": "seed_coder", "task_id": "T5"},
    )
    orch._materialize_workspace_artifact(
        "test_game.py",
        {"files": [{"filename": "test_game.py", "content": "from game import size\n\n\ndef test_size() -> None:\n    assert size() == 10\n"}]},
        writer={"agent": "seed_tester", "task_id": "T10"},
    )
    sync_hypergraph_matrix(ws, orch.matrix_path)

    report = orch._run_verification_step(
        {"task_id": "T5", "target_node": "game.py", "assigned_agent": "seed_coder"}, include_docs=False
    )

    assert report["status"] == "FAIL"
    assert report["failed_file"] == "test_game.py"
    assert report["failed_agent"] == "seed_tester"


def test_explicit_path_never_routes_to_a_file_whose_name_merely_contains_it(tmp_path: Path) -> None:
    """2026-11-13: T4 on `tictoc_config.py` was sent to `config.py` by a substring match in the description."""
    orch = _orch(tmp_path)
    ws = orch.workspace_dir
    _write(ws, "config.py", "SEED = 1\n")
    sync_hypergraph_matrix(ws, orch.matrix_path)

    node_id, path = orch._resolve_target_node(
        "tictoc_config.py", task={"description": "Moduł konfiguracji `tictoc_config.py` z klasą Config"}
    )
    by_desc, path_by_desc = orch._resolve_target_node("v9", task={"description": "Uzupełnij tictoc_config.py."})

    assert path == "tictoc_config.py" and path_by_desc == "tictoc_config.py"
    nodes = json.loads(orch.matrix_path.read_text(encoding="utf-8"))["nodes"]
    assert nodes[node_id]["path"] == "tictoc_config.py" and by_desc == node_id


def test_cross_role_and_off_target_writes_are_logged(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    orch._materialize_workspace_artifact(
        "game.py",
        {"files": [
            {"filename": "game.py", "content": "X = 1\n"},
            {"filename": "test_game.py", "content": "def test_x() -> None:\n    pass\n"},
        ]},
        writer={"agent": "seed_coder", "task_id": "T5"},
    )

    events = json.loads(orch.evolution_history_path.read_text(encoding="utf-8"))["events"]
    kinds = {e["type"]: e for e in events}
    assert kinds["CROSS_ROLE_WRITE"]["files"] == ["test_game.py"]
    assert kinds["OFF_TARGET_WRITE"]["files"] == ["test_game.py"]
