"""State files at the start of a run, the resolution of the target node of a task and the status of a crashed run."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adk.orchestrator import NeuroSymbolicOrchestrator
from tests.support.adk_sandbox import _clone_adk_env


def test_state_files_initialized():
    root = Path(__file__).resolve().parent.parent.parent / "adk" / "state"
    expected = [
        "task_queue.json",
        "agent_registry.json",
        "validation_report.json",
        "failure_ledger.json",
        "evolution_history.json",
        "hitl_flag.json",
    ]
    for filename in expected:
        file_path = root / filename
        assert file_path.exists(), f"Missing state file: {filename}"
        data = json.loads(file_path.read_text(encoding="utf-8"))
        assert data is not None


def test_orchestrator_resolve_target_node(tmp_path: Path):
    """Targets are read from H: a planned path, the planned file a label's description names, the chapter a thesis
    task names, a test named without its directory. No role aliases, no opaque ids, no guessing (Audit VIII C1)."""
    import pytest

    from tests.support.planned_projects import with_plan

    adk_dir = _clone_adk_env(tmp_path)
    orch = NeuroSymbolicOrchestrator(adk_root=adk_dir, provider="mock")
    core = '"""Core."""\n\n\ndef play(seed: int) -> int:\n    """Score."""\n'
    tasks = [{"task_id": "T2", "target_node": "tests/test_core.py", "description": "tests", "assigned_agent": "seed_tester"}]
    with_plan(orch, {"core.py": core}, "core.py:play", tasks, [{"index": 2, "title": "Stan wiedzy", "focus": "literatura"}])

    assert orch._resolve_target_node("core.py") == ("core.py", "core.py")
    assert orch._resolve_target_node("./workspace/core.py") == ("core.py", "core.py")
    assert orch._resolve_target_node("node_core", task={"description": "Fix play() in core.py"}) == ("core.py", "core.py")
    assert orch._resolve_target_node("test_core.py") == ("tests/test_core.py", "tests/test_core.py")
    assert orch._resolve_target_node("thesis.md", task={"description": "Write Chapter 2"}) == ("thesis.md#ch2", "thesis.md")
    assert orch._resolve_target_node("thesis.md#ch2") == ("thesis.md#ch2", "thesis.md")
    # A path the plan does not know stays what it is: the spec gate judges what is written there.
    assert orch._resolve_target_node("src/models/dqn.py") == ("src/models/dqn.py", "src/models/dqn.py")
    with pytest.raises(ValueError):
        orch._resolve_target_node("v7")
    assert orch._resolve_target_node("v7", fallback="core.py") == ("core.py", "core.py")


def test_crashed_orchestrator_still_gives_the_run_a_status(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import MagicMock

    from adk.benchmarks import run_benchmark_suite, runner

    monkeypatch.setattr(runner.NeuroSymbolicOrchestrator, "run", MagicMock(side_effect=RuntimeError("narzędzie padło")))
    res = run_benchmark_suite(task_keys=["2"], provider="mock", output_root=tmp_path / "out")

    assert res["tasks"][0]["orchestrator_status"] == "CRASHED"
    assert "narzędzie padło" in res["tasks"][0]["orchestrator_error"]
