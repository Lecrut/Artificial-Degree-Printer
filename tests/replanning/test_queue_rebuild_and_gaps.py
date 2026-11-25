"""Rebuilding the queue and delivering with gaps: oscillating failures, an exhausted budget lists every gap, critic findings become tasks."""

from __future__ import annotations

import json
from pathlib import Path

from adk.orchestrator import NeuroSymbolicOrchestrator
from tests.support.adk_sandbox import _clone_adk_env
from tests.support.run_loop_fixtures import _RUFF_F841, _orch_with_workspace


def test_rebuild_queue_detects_oscillating_failures(tmp_path: Path):
    adk_dir = _clone_adk_env(tmp_path)
    orch = NeuroSymbolicOrchestrator(adk_root=adk_dir, provider="mock")
    audits = iter(
        [
            {"pytest_status": "FAIL", "pytest_errors": [_RUFF_F841.format(name="width", line=19)]},
            {"pytest_status": "FAIL", "pytest_errors": ["FAILED test_core.py::test_draw - AssertionError"]},
            {"pytest_status": "FAIL", "pytest_errors": [_RUFF_F841.format(name="plot_df", line=17)]},
            {"pytest_status": "FAIL", "pytest_errors": [_RUFF_F841.format(name="bars", line=24)]},
        ]
    )
    orch._audit_factual_state = lambda _report: next(audits)
    seen: list[str] = []
    assert "tasks" in orch._rebuild_queue({}, 0, seen)
    assert "tasks" in orch._rebuild_queue({}, 1, seen)
    # The third audit repeats the first one under another variable name (A -> B -> A), but a repeat stops the run
    # only from the third rebuild on (2026-11-24: runs close to done were cut off too early).
    assert "tasks" in orch._rebuild_queue({}, 2, seen)
    assert "stop" in orch._rebuild_queue({}, 3, seen)


def test_exhausted_budget_delivers_work_with_listed_gaps(tmp_path: Path):
    orch = _orch_with_workspace(tmp_path, {"thesis.md": "## Rozdział 1: Wstęp\n\nTekst.\n"})
    orch._audit_factual_state = lambda _report: {
        "pytest_status": "FAIL",
        "pytest_errors": ["FAILED test_core.py::test_draw - AssertionError"],
        "chapters_missing": [6],
        "trigger_issues": ["Wskaźnik remisów 12,6% opisano jako wysoki."],
    }
    res = orch._rebuild_queue({"status": "FAIL"}, 4, [])
    stop = res["stop"]
    assert stop["status"] == "COMPLETED_WITH_GAPS"
    kinds = {g["kind"] for g in stop["gaps"]}
    assert {"kod", "rozdział", "ustalenie weryfikacji"} <= kinds

    thesis = (orch.workspace_dir / "thesis.md").read_text(encoding="utf-8")
    assert "Braki i ograniczenia realizacji" in thesis
    assert "Brak rozdziału 6" in thesis
    report = json.loads(orch.validation_report_path.read_text(encoding="utf-8"))
    assert len(report["gaps"]) == len(stop["gaps"])
    hitl = json.loads(orch.hitl_flag_path.read_text(encoding="utf-8")) if orch.hitl_flag_path.exists() else {}
    assert hitl.get("current_gate") != "GATE_QUEUE_REBUILD_EXHAUSTED"


def test_critic_findings_become_tasks_with_ids(tmp_path: Path):
    from tests.support.planned_projects import with_plan

    orch = _orch_with_workspace(tmp_path, {"plot_results.py": "X = 1\n", "thesis.md": "## A\n"})
    with_plan(orch, {"plot_results.py": '"""Plots."""\nX: int = 1\n'})
    tasks = orch._tasks_from_audit(
        {
            "pytest_status": "PASS",
            "csv_columns": ["method", "metric", "value"],
            "trigger_issues": [
                "W pliku plot_results.py warunek if 'unstack' jest zawsze prawdziwy.",
                "Rozdział 6 twierdzi, że nie było powtórzeń, a kod robi 50.",
                "Brak liczb w zdaniach o wynikach.",
            ],
        },
        2,
    )
    by_target = {t["target_node"]: t for t in tasks}
    assert "plot_results.py" in by_target
    critic = next(t for t in tasks if t["task_id"].endswith("_CRITIC"))
    assert "[K1]" in critic["description"] and "[K2]" in critic["description"]
    assert critic["assigned_agent"] == "seed_writer"
