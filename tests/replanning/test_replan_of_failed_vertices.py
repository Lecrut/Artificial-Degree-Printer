"""The re-plan of the failed vertices after the queue: the dossier it is given, what waits for what failed, which verified vertex may be reopened (once, one per round) and when the run ends with gaps."""

from __future__ import annotations

from pathlib import Path

from adk.hypergraph.schedule import FAILED
from adk.orchestration.common import _RunState
from adk.orchestration.fragment_replan import _latest_errors
from tests.support.failed_vertex_project import _TASKS, _events, _planned, _seen
from tests.support.queue_state import _state


def _answer(orch, tasks: list[dict]) -> list[dict]:
    sent: list[dict] = []
    orch._call_agent = lambda _md, payload, **_k: sent.append(payload) or {"status": "ok", "output": {"tasks": tasks}}
    return sent


def test_the_failed_part_is_re_planned_from_its_dossier(tmp_path: Path):
    orch, h = _planned(tmp_path)
    h.vertices["config.py"].state = FAILED
    h.vertices["config.py"].history.append({"task_id": "T1", "issues": ["ANSWER_REJECTED: SyntaxError"]})
    h.vertices["thesis.md#ch1"].state = "verified"
    sent: list[dict] = []
    answer = {"tasks": [
        {"target_node": "config.py", "description": "Write the constants only", "assigned_agent": "seed_coder"},
        {"target_node": "thesis.md", "description": "Chapter 1: rewrite", "assigned_agent": "seed_writer"},
        {"target_node": "nowhere.py", "description": "?"},
    ]}
    orch._call_agent = lambda _md, payload, **_k: sent.append(payload) or {"status": "ok", "output": answer}
    seen = _seen(orch)
    state = _RunState(user_prompt="p", max_retries=2, multi_cycle_waves=True, tasks=[])
    result = orch._replan_failed(state)
    assert [(t["task_id"], t["target_node"]) for t in result["tasks"]] == [("R1_1", "config.py")]
    assert state.tasks == result["tasks"]
    dossier = sent[0]["repair_dossier"]
    assert [e["vertex"] for e in dossier["failed"]] == ["config.py"]
    assert dossier["failed"][0]["history"][-1]["issues"] == ["ANSWER_REJECTED: SyntaxError"]
    assert "thesis.md#ch1" in dossier["verified_do_not_touch"] and "core.py" in dossier["failed"][0]["waiting_on_it"]
    replanned = [e for e in _events(orch, seen) if e["event"] == "REPLANNED"]
    assert replanned and replanned[0]["tasks"] == ["R1_1"] and len(replanned[0]["dropped"]) == 2


def test_re_planning_without_progress_ends_the_run_with_gaps(tmp_path: Path):
    orch, h = _planned(tmp_path)
    h.vertices["config.py"].state = FAILED
    orch._call_agent = lambda *_a, **_k: {"status": "ok", "output": {"tasks": []}}
    orch._audit_factual_state = lambda _report: {}
    orch._finalize_with_gaps = lambda _audit, _report: {"gaps": [{"kind": "kod", "detail": "config.py"}], "pdf_ok": False}
    orch._shout_problem_stop = lambda _msg: None
    state = _RunState(user_prompt="p", max_retries=2, multi_cycle_waves=True, tasks=[])
    assert all("tasks" in orch._replan_failed(state) for _ in range(3))
    stop = orch._replan_failed(state)["stop"]
    assert stop["status"] == "COMPLETED_WITH_GAPS" and stop["reason"] == "REPLAN_EXHAUSTED" and stop["failed_vertices"] == ["config.py"]


def test_nothing_failed_means_no_re_plan(tmp_path: Path):
    orch, _h = _planned(tmp_path)
    orch._call_agent = lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("no planner call expected"))
    assert orch._replan_failed(_RunState(user_prompt="p", max_retries=2, multi_cycle_waves=True, tasks=[])) is None


def test_reopening_a_verified_vertex_is_not_standing_still(tmp_path: Path):
    orch, h = _planned(tmp_path)
    h.vertices["config.py"].state = FAILED
    orch._call_agent = lambda *_a, **_k: {"status": "ok", "output": {"tasks": []}}
    state = _RunState(user_prompt="p", max_retries=2, multi_cycle_waves=True, tasks=[])
    orch._replan_failed(state)
    h.vertices["core.py"].state = "verified"
    orch._replan_failed(state)  # 6 verified-so-far counted
    h.vertices["core.py"].state = FAILED  # 01: a verified file reopened and failing again: 6 -> 7 -> 6
    orch._replan_failed(state)
    assert orch._replan_progress[-1] >= orch._replan_progress[0]


def test_latest_errors_skip_planner_entries_and_older_attempts():
    history = [
        {"task_id": "R2_1", "issues": ["old NameError"]},
        {"task_id": "R4_1", "issues": ["Metric 'mean_td_error' declared in the plan was not measured."]},
        {"task_id": "REPLAN", "issues": ["Interface of x.py changed by the re-plan."]},
    ]
    assert _latest_errors(history) == ["Metric 'mean_td_error' declared in the plan was not measured."]
    assert _latest_errors([]) == []


def test_the_dossier_carries_the_code_and_state_of_the_dependencies(tmp_path: Path):
    orch, h = _planned(tmp_path)
    (orch.workspace_dir / "config.py").write_text("X = 1\n", encoding="utf-8")
    h.vertices["config.py"].state = "verified"
    h.vertices["core.py"].state = FAILED
    sent = _answer(orch, [])
    orch._replan_failed(_state([]))
    deps = sent[0]["repair_dossier"]["failed"][0]["dependencies"]
    assert deps["config.py"] == {"state": "verified", "source": "X = 1\n"}


def test_a_waiting_test_of_a_failed_module_takes_the_fix_instead_of_dropping_it(tmp_path: Path):
    orch, h = _planned(tmp_path)
    h.vertices["core.py"].state = FAILED
    queue = [{**_TASKS[2], "status": "WAITING"}]
    _answer(orch, [{"target_node": "tests/test_core.py", "description": "Pass an array, not 0", "assigned_agent": "seed_tester"}])
    result = orch._replan_failed(_state(queue))
    assert result["tasks"] == [] and queue[0]["description"] == "Pass an array, not 0" and queue[0]["force_ready"] is True


def test_a_fix_of_a_test_runs_once_although_its_module_is_not_verified(tmp_path: Path):
    orch, h = _planned(tmp_path)
    h.vertices["core.py"].state = FAILED
    task = {**_TASKS[2], "status": "WAITING", "force_ready": True}
    state = _state([task])
    assert [t["task_id"] for _i, t in orch._task_order(state)][:1] == ["T3"]
    assert "force_ready" not in task
    task["status"] = "WAITING"
    assert list(orch._task_order(state)) == []  # the second time it waits for its module again


def test_a_new_test_task_of_a_failed_module_goes_first(tmp_path: Path):
    orch, h = _planned(tmp_path)
    h.vertices["core.py"].state = FAILED
    _answer(orch, [
        {"target_node": "core.py", "description": "rewrite", "assigned_agent": "seed_coder"},
        {"target_node": "tests/test_core.py", "description": "fix the test", "assigned_agent": "seed_tester"},
    ])
    tasks = orch._replan_failed(_state([]))["tasks"]
    assert [t["target_node"] for t in tasks] == ["tests/test_core.py", "core.py"] and tasks[0]["force_ready"]


def test_one_verified_dependency_is_reopened_and_never_twice(tmp_path: Path):
    orch, h = _planned(tmp_path)
    h.vertices["config.py"].state = "verified"
    h.vertices["core.py"].state = FAILED
    _answer(orch, [{"target_node": "config.py", "description": "return the value", "assigned_agent": "seed_coder"}])
    result = orch._replan_failed(_state([]))
    assert [t["target_node"] for t in result["tasks"]] == ["config.py"] and h.vertices["config.py"].state == "stale"
    h.vertices["config.py"].state = "verified"
    h.vertices["core.py"].state = FAILED
    assert orch._replan_failed(_state([]))["tasks"] == [] and h.vertices["config.py"].state == "verified"


def test_a_verified_vertex_outside_the_dossier_stays_closed_and_only_one_is_reopened(tmp_path: Path):
    orch, h = _planned(tmp_path)
    h.vertices["config.py"].state = "verified"
    h.vertices["tests/test_core.py"].state = "verified"
    h.vertices["core.py"].state = FAILED
    _answer(orch, [
        {"target_node": "tests/test_core.py", "description": "x", "assigned_agent": "seed_tester"},
        {"target_node": "config.py", "description": "y", "assigned_agent": "seed_coder"},
        {"target_node": "config.py", "description": "z", "assigned_agent": "seed_coder"},
    ])
    result = orch._replan_failed(_state([]))
    assert [t["target_node"] for t in result["tasks"]] == ["config.py"]
    assert h.vertices["tests/test_core.py"].state == "verified"


def test_a_replan_interface_for_a_module_outside_the_plan_is_logged_not_swallowed(tmp_path: Path, monkeypatch):
    orch, h = _planned(tmp_path)
    h.vertices["core.py"].state = FAILED
    events: list[tuple] = []
    monkeypatch.setattr(orch.logger, "log_event", lambda name, **kw: events.append((name, kw)))
    changed = orch._replan_interfaces(h, {"interfaces": {"new_helper.py": "def f() -> int:\n    ...\n"}}, ["core.py"], {}, {})
    assert changed == []
    assert [(n, kw["module"], kw["reason"]) for n, kw in events] == [("SPEC_AMEND_SKIPPED", "new_helper.py", "not a module of the plan")]


def test_a_caller_named_in_the_errors_of_a_failed_module_is_in_the_dossier_and_reopenable(tmp_path: Path):
    orch, h = _planned(tmp_path)
    (orch.workspace_dir / "core.py").write_text("def f(state):\n    return state\n", encoding="utf-8")
    h.vertices["config.py"].state = FAILED
    h.vertices["core.py"].state = "verified"  # core.py uses config.py: it is above it
    h.vertices["config.py"].history[:] = [{"task_id": "T1", "issues": ["Pytest failure:\ncore.py:3: in f\nconfig.py:1: in g\nE TypeError"]}]
    sent = _answer(orch, [{"target_node": "core.py", "description": "pass a tuple", "assigned_agent": "seed_coder"}])
    result = orch._replan_failed(_state([]))
    entry = sent[0]["repair_dossier"]["failed"][0]
    assert entry["dependents"]["core.py"]["state"] == "verified"
    assert [t["target_node"] for t in result["tasks"]] == ["core.py"] and h.vertices["core.py"].state == "stale"


def test_a_neighbour_the_errors_do_not_name_is_not_a_suspect(tmp_path: Path):
    orch, h = _planned(tmp_path)
    h.vertices["config.py"].state = FAILED
    h.vertices["core.py"].state = "verified"
    h.vertices["config.py"].history[:] = [{"task_id": "T1", "issues": ["Ruff lint failure: config.py:1:1: F821 x"]}]
    sent = _answer(orch, [{"target_node": "core.py", "description": "x", "assigned_agent": "seed_coder"}])
    result = orch._replan_failed(_state([]))
    assert sent[0]["repair_dossier"]["failed"][0]["dependents"] == {} and result["tasks"] == []


def test_a_file_name_inside_another_name_is_not_a_mention():
    from adk.orchestration.fragment_replan import _mentioned

    assert _mentioned("tests\\test_trainer.py:13: in test_x\ntrainer.py:63: in f", "trainer.py")
    assert not _mentioned("tests\\test_trainer.py:13: in test_x", "trainer.py")
    assert _mentioned("tests\\test_trainer.py:13: in test_x", "tests/test_trainer.py")
