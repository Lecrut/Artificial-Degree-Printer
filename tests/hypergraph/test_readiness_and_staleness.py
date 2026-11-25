"""Readiness and staleness: a module runs after the modules it uses, a test waits for its module to be verified, a failure blocks only what depends on it, results chapters wait for current results and a code change makes results stale."""

from __future__ import annotations

from pathlib import Path

from adk.hypergraph import load
from adk.hypergraph.schedule import FAILED, readiness, vertex_of
from adk.orchestration.common import _RunState
from tests.support.failed_vertex_project import _TASKS, _planned
from tests.support.game_project import _GAME, _GAME_IMPL
from tests.support.game_project import _planned as _planned_game_project
from tests.support.sample_research_project import _CONFIG, _h, _spec_orch


def _run_order(orch, tasks, fail: set[str] = frozenset()) -> list[str]:
    state = _RunState(user_prompt="p", max_retries=1, multi_cycle_waves=True, tasks=tasks)
    order = []
    for _idx, task in orch._task_order(state):
        order.append(task["task_id"])
        task["status"] = "FAILED" if task["task_id"] in fail else "DONE"
        if task["task_id"] not in fail:
            vertex = orch._task_vertex(task)
            orch._set_vertex_state(vertex, "impl")
    return order


def _tasks(*pairs):
    return [{"task_id": tid, "target_node": target, "description": f"implement {target}", "status": "TODO"} for tid, target in pairs]


def test_a_code_change_after_the_experiment_makes_the_results_stale_and_reruns_them(tmp_path: Path):
    orch = _spec_orch(tmp_path)
    runs: list[str] = []
    orch._refresh_experiment_after_code = lambda node: runs.append(node)
    orch._record_data_produced()
    assert load(orch.hypergraph_path).edges["R:run"].fingerprint
    orch._ensure_fresh_results()
    assert runs == []  # nothing changed since the results were produced
    (orch.workspace_dir / "src/config.py").write_text(_CONFIG.replace("3", "5"), encoding="utf-8")
    orch._ensure_fresh_results()
    assert runs == ["src/experiment.py"]
    assert any('"DATA_STALE"' in line for line in orch.logger.events_path.read_text(encoding="utf-8").splitlines())


def test_a_module_runs_after_the_modules_it_uses_whatever_the_plan_order(tmp_path: Path):
    orch = _spec_orch(tmp_path)
    tasks = _tasks(("T1", "src/experiment.py"), ("T2", "src/config.py"), ("T3", "src/data_generator.py"))
    assert _run_order(orch, tasks) == ["T2", "T3", "T1"]


def test_a_failure_blocks_only_what_depends_on_it_and_nothing_is_lost(tmp_path: Path):
    """X1: the failed SKELETON blocked every later task on the entrypoint file, and rebuilt queues dropped them."""
    orch = _spec_orch(tmp_path)
    tasks = _tasks(("T1", "src/config.py"), ("T2", "src/data_generator.py"), ("T3", "src/config.py"))
    # the second task on the same file still runs (no block by file); once config has code, its user may run
    assert _run_order(orch, tasks, fail={"T1"}) == ["T1", "T3", "T2"]

    orch = _spec_orch(tmp_path / "again")
    tasks = _tasks(("T1", "src/config.py"), ("T2", "src/data_generator.py"), ("T3", "src/config.py"))
    assert _run_order(orch, tasks, fail={"T1", "T3"}) == ["T1", "T3"]
    assert tasks[1]["status"] == "WAITING"  # the generator waits for config, it is not dropped
    carried = orch._carry_over(tasks)
    assert [t["task_id"] for t in carried] == ["T2"] and carried[0]["status"] == "TODO"


def test_a_results_chapter_waits_for_current_results():
    """01: the conclusions claimed the thesis was not confirmed while no results existed."""
    h, _ = _h()
    assert vertex_of(h, "thesis.md", "[Increment 3] Write Chapter 4 (Results) of thesis.md") == "thesis.md#ch4"
    assert readiness(h, "thesis.md#ch4", set()) == ["results.csv: the experiment has not produced current results"]
    assert readiness(h, "thesis.md#ch1", set()) == []
    h.vertices["results.csv"].state = "verified"
    assert readiness(h, "thesis.md#ch4", set()) == []


def test_a_test_waits_for_its_module_to_be_verified(tmp_path: Path):
    _orch_, h = _planned(tmp_path)
    h.vertices["core.py"].state = "impl"
    assert readiness(h, "tests/test_core.py", set()) == ["core.py is not verified yet"]
    h.vertices["core.py"].state = "verified"
    assert readiness(h, "tests/test_core.py", set()) == []


def test_a_module_never_builds_on_a_failed_one(tmp_path: Path):
    _orch_, h = _planned(tmp_path)
    assert "config.py" in h.edges["I:core.py"].spec.get("uses", {})
    h.vertices["config.py"].state = FAILED
    assert readiness(h, "core.py", set()) == ["config.py failed; it waits for its re-plan"]


def test_a_task_failing_for_another_vertex_is_deferred_to_it(tmp_path: Path):
    orch, h = _planned(tmp_path)
    test_task = _TASKS[2]
    blamed = orch._mark_failed({"failed_file": "core.py"}, test_task)
    assert blamed == "core.py" and h.vertices["core.py"].state == FAILED
    assert orch._waits_on_failed(test_task)


def test_the_experiment_does_not_run_while_a_module_it_runs_is_a_stub(tmp_path: Path):
    orch, _ = _planned_game_project(tmp_path)
    (orch.workspace_dir / "game.py").write_text(_GAME + "    raise NotImplementedError\n", encoding="utf-8")
    assert orch._experiment_still_stubbed() is True
    (orch.workspace_dir / "game.py").write_text(_GAME_IMPL, encoding="utf-8")
    assert orch._experiment_still_stubbed() is False
