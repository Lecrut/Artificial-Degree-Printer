"""Stage 0 of Audit IV (2026-11-13 run): the harness itself produced most failures. Each test is one of them."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from adk.orchestration.common import MaterializationError
from adk.orchestrator import NeuroSymbolicOrchestrator
from adk.tools.building.ast_editor import edit_ast_node
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


GAME = "class Game:\n    def reset(self) -> None:\n        raise NotImplementedError\n"
# The docstring the model broke at 12:28 on 2026-11-13: a stray `\"\"\"` line after a closed docstring.
BROKEN_GAME = 'class Game:\n    def reset(self) -> None:\n        """Resets the board."""\n"""\n        self.board = []\n'


def test_unparsable_python_never_reaches_the_disk(tmp_path: Path) -> None:
    orch = _orch(tmp_path)

    with pytest.raises(MaterializationError, match=r"game\.py:4"):
        orch._materialize_workspace_artifact("game.py", {"files": [{"filename": "game.py", "content": BROKEN_GAME}]})

    assert not (orch.workspace_dir / "game.py").exists()


def test_rejected_answer_is_retried_once_at_the_same_agent_with_the_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    orch = _orch(tmp_path)
    calls: list[dict[str, Any]] = []

    def fake_call(_agent_md: Path, payload: dict[str, Any], **_: Any) -> dict[str, Any]:
        calls.append(payload)
        content = BROKEN_GAME if len(calls) == 1 else GAME
        return {"output": {"files": [{"filename": "game.py", "content": content}]}}

    monkeypatch.setattr(orch, "_call_agent", fake_call)
    orch._execute_builder_step({"task_id": "T1", "target_node": "game.py", "assigned_agent": "seed_coder"}, model_tier="SML")

    assert len(calls) == 2
    assert "rejected_answer" not in calls[0]
    assert "game.py:4" in calls[1]["rejected_answer"]["error"]
    assert (orch.workspace_dir / "game.py").read_text(encoding="utf-8") == GAME


def test_method_edit_keeps_its_class_indentation(tmp_path: Path) -> None:
    target = tmp_path / "game.py"
    target.write_text(GAME, encoding="utf-8")

    res = edit_ast_node(target, "Game.reset", "    def reset(self) -> None:\n        self.board = []\n")

    assert res["status"] == "ok", res
    assert "self.board = []" in target.read_text(encoding="utf-8")


def test_unparsable_file_tells_the_agent_to_return_the_whole_file_and_accepts_it(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    (orch.workspace_dir / "game.py").write_text(BROKEN_GAME, encoding="utf-8")
    edit = {"ast_edits": [{"symbol": "Game.reset", "file": "game.py", "code": "def reset(self) -> None:\n    self.board = []\n"}]}

    with pytest.raises(MaterializationError, match=r"does not parse now.*whole corrected file.*'files'"):
        orch._materialize_workspace_artifact("game.py", edit)

    orch._materialize_workspace_artifact("game.py", {"files": [{"filename": "game.py", "content": GAME}]})
    assert (orch.workspace_dir / "game.py").read_text(encoding="utf-8") == GAME


def test_empty_file_and_flat_filename_content_are_accepted(tmp_path: Path) -> None:
    orch = _orch(tmp_path)

    orch._materialize_workspace_artifact("src/__init__.py", {"files": [{"filename": "src/__init__.py", "content": ""}]})
    orch._materialize_workspace_artifact("config.py", {"filename": "config.py", "content": "SEED = 1\n"})

    assert (orch.workspace_dir / "src" / "__init__.py").read_text(encoding="utf-8") == ""
    assert (orch.workspace_dir / "config.py").read_text(encoding="utf-8") == "SEED = 1\n"


def test_modules_inside_a_package_are_imported_by_their_dotted_path(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    (ws / "src").mkdir(parents=True)
    (ws / "src" / "__init__.py").write_text("", encoding="utf-8")
    (ws / "src" / "game.py").write_text("def size() -> int:\n    return 9\n", encoding="utf-8")
    (ws / "test_game.py").write_text("from src.game import size\n\n\ndef test_size() -> None:\n    assert size() == 9\n", encoding="utf-8")

    res = test_runner.run_isolated_tests(ws, verification_dir=tmp_path / "no_validators")

    assert res["status"] == "PASS", res["errors"]
    assert not [e for e in res["errors"] if e.startswith("Import error")]


def test_symbols_qualified_with_module_or_path_land_in_the_file(tmp_path: Path) -> None:
    """2026-11-14: `random_agent.RandomAgent.__init__`, `train.py:main`, `src/exp/runner.run_all` were rejected."""
    orch = _orch(tmp_path)
    (orch.workspace_dir / "src").mkdir()
    (orch.workspace_dir / "game.py").write_text(GAME, encoding="utf-8")
    (orch.workspace_dir / "src" / "runner.py").write_text("def run_all() -> None:\n    pass\n", encoding="utf-8")

    orch._materialize_workspace_artifact("game.py", {"ast_edits": [
        {"symbol": "game.Game.reset", "file": "game.py", "code": "def reset(self) -> None:\n    self.board = []\n"},
        {"symbol": "src/runner.py:run_all", "code": "def run_all() -> int:\n    return 1\n"},
    ]})

    assert "self.board = []" in (orch.workspace_dir / "game.py").read_text(encoding="utf-8")
    assert "return 1" in (orch.workspace_dir / "src" / "runner.py").read_text(encoding="utf-8")


def test_two_test_files_with_one_basename_are_both_collected(tmp_path: Path) -> None:
    """2026-11-14 (task 02): `test_config.py` and `tests/test_config.py` broke collection in every verification."""
    ws = tmp_path / "ws"
    (ws / "tests").mkdir(parents=True)
    (ws / "config.py").write_text("SEED = 1\n", encoding="utf-8")
    for rel in ("test_config.py", "tests/test_config.py"):
        (ws / rel).write_text("from config import SEED\n\n\ndef test_seed() -> None:\n    assert SEED == 1\n", encoding="utf-8")

    res = test_runner.run_isolated_tests(ws, verification_dir=tmp_path / "none")

    assert res["status"] == "PASS", res["errors"]


def test_benchmark_task_logs_live_into_its_own_folder(tmp_path: Path) -> None:
    """§VI.9a P6: per-task harness log and trace, written live, copied to benchmarks/<slug>/logs/; afterwards the
    logger is back on the default directory."""
    import os

    from adk.benchmarks import run_benchmark_suite
    from adk.core.logger import get_process_logger

    res = run_benchmark_suite(task_keys=["2"], provider="mock", output_root=tmp_path / "out")

    task_logs = tmp_path / "out" / "02_ml_anomaly_detection" / "logs"
    assert "[ORCHESTRATOR_START]" in (task_logs / "harness_process.log").read_text(encoding="utf-8")
    assert (task_logs / "agent_trace.jsonl").stat().st_size > 0
    assert res["tasks"][0]["orchestrator_status"]
    assert get_process_logger().log_dir == Path(os.environ["HARNESS_LOG_DIR"])


def test_interrupted_run_leaves_a_status(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import MagicMock

    from adk.benchmarks import run_benchmark_suite, runner

    monkeypatch.setattr(runner.NeuroSymbolicOrchestrator, "run", MagicMock(side_effect=KeyboardInterrupt()))
    res = run_benchmark_suite(task_keys=["2"], provider="mock", output_root=tmp_path / "out")

    assert res["status"] == "INTERRUPTED"
    assert res["tasks"][0]["orchestrator_status"] == "INTERRUPTED"
    assert json.loads((tmp_path / "out" / "benchmark_summary.json").read_text(encoding="utf-8"))["status"] == "INTERRUPTED"
