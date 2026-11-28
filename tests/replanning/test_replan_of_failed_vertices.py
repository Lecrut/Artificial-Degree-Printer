"""The re-plan of the failed vertices after the queue: the dossier it is given, what waits for what failed, which verified vertex may be reopened (once, one per round) and when the run ends with gaps."""

from __future__ import annotations

from pathlib import Path

from adk.hypergraph.schedule import FAILED
from adk.orchestration.common import _RunState
from adk.orchestration.recovery.replan import _latest_errors
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
    assert dossier["failed"][0]["latest_errors"] == ["ANSWER_REJECTED: SyntaxError"] and dossier["failed"][0]["history"] == []  # said once (§XXXVIII P1)
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
    from adk.orchestration.recovery.replan import _mentioned

    assert _mentioned("tests\\test_trainer.py:13: in test_x\ntrainer.py:63: in f", "trainer.py")
    assert not _mentioned("tests\\test_trainer.py:13: in test_x", "trainer.py")
    assert _mentioned("tests\\test_trainer.py:13: in test_x", "tests/test_trainer.py")


_SAME_ERROR = "Pytest failure:\ntests/test_core.py:35: in test_act\ncore.py:42: in act\nE   IndexError: index 2 is out of bounds"


def test_the_dossier_says_when_the_last_re_plan_did_not_move_an_error(tmp_path: Path):
    """§XXX P9b, 01: rounds 2-4 changed interfaces against an unchanged `.FF..`; the planner now hears that it stands still."""
    orch, h = _planned(tmp_path)
    h.vertices["core.py"].state = FAILED
    h.vertices["core.py"].history[:] = [{"task_id": "T3", "issues": [_SAME_ERROR]}]
    first = orch._repair_dossier(h, ["core.py"])["failed"][0]
    assert first["same_error_as_last_round"] is False  # nothing to compare with yet
    assert orch._repair_dossier(h, ["core.py"])["failed"][0]["same_error_as_last_round"] is True
    h.vertices["core.py"].history[:] = [{"task_id": "R1_1", "issues": [_SAME_ERROR.replace("IndexError: index 2", "KeyError: 2")]}]
    assert orch._repair_dossier(h, ["core.py"])["failed"][0]["same_error_as_last_round"] is False  # a new error is a new problem


def test_an_interface_change_is_refused_for_a_module_whose_error_did_not_move(tmp_path: Path, monkeypatch):
    orch, h = _planned(tmp_path)
    h.vertices["core.py"].state = FAILED
    events: list[tuple] = []
    monkeypatch.setattr(orch.logger, "log_event", lambda name, **kw: events.append((name, kw)))
    dossier = {"failed": [{"vertex": "core.py", "same_error_as_last_round": True}]}
    out = {"interfaces": {"core.py": "def f() -> int:\n    ...\n"}}
    assert orch._replan_interfaces(h, out, ["core.py"], {}, {}, dossier) == []
    assert events == [("SPEC_AMEND_SKIPPED", {"module": "core.py", "task_id": "REPLAN", "reason": "same error as after the last re-plan"})]


def test_the_task_planner_prompt_names_the_unmoved_error_flag():
    text = (Path(__file__).resolve().parents[2] / "adk" / "agents" / "planning" / "task_planner.md").read_text(encoding="utf-8")
    assert "`same_error_as_last_round`" in text


def _failed_for_the_tests_fault(h, blamed_state: str):
    h.vertices["core.py"].state = "impl"  # the module's task failed, its own vertex is unfinished
    h.vertices["tests/test_core.py"].state = blamed_state
    return _state([{"task_id": "R2_1", "target_node": "core.py", "assigned_agent": "seed_coder", "status": "FAILED",
                    "repair_attempts": 3, "blamed": "tests/test_core.py"}])


def test_a_task_that_failed_for_another_vertexs_fault_runs_again_once_that_vertex_is_repaired(tmp_path: Path):
    """§XXXII P1, 01 of 2026-11-26: `R2_1` (the experiment) failed on `tests/test_environment.py`; `R2_2` repaired the test;
    the experiment stayed `impl` with no task and the run ended with it as a gap."""
    orch, h = _planned(tmp_path)
    state = _failed_for_the_tests_fault(h, "verified")
    seen = _seen(orch)
    assert orch._requeue_blamed(state) == ["R2_1"]
    task = state.tasks[0]
    assert task["status"] == "TODO" and task["repair_attempts"] == 0 and task["requeued"] is True
    assert [e["event"] for e in _events(orch, seen)] == ["TASK_REQUEUED"]
    task["status"] = "FAILED"  # it fails again: not a third time
    assert orch._requeue_blamed(state) == []


def test_a_task_is_not_run_again_while_the_vertex_at_fault_is_still_broken(tmp_path: Path):
    orch, h = _planned(tmp_path)
    for broken in ("failed", "written", "spec"):
        state = _failed_for_the_tests_fault(h, broken)
        assert orch._requeue_blamed(state) == [] and state.tasks[0]["status"] == "FAILED"


def test_a_vertex_that_was_verified_meanwhile_or_failed_itself_is_left_alone(tmp_path: Path):
    orch, h = _planned(tmp_path)
    state = _failed_for_the_tests_fault(h, "verified")
    h.vertices["core.py"].state = "verified"
    assert orch._requeue_blamed(state) == []
    h.vertices["core.py"].state = FAILED  # the re-plan takes it
    assert orch._requeue_blamed(state) == []


def test_an_interface_the_planner_wrote_with_bodies_is_kept_without_them(tmp_path: Path, monkeypatch):
    """§XXXVII.6: the planner's 50-line implementations (with the bugs of the code) went into `interfaces` as they were."""
    orch, h = _planned(tmp_path)
    h.vertices["core.py"].state = FAILED
    seen: dict[str, str] = {}
    monkeypatch.setattr(orch, "_apply_amendment", lambda rel, source, *_a: seen.setdefault(rel, source) and [])
    interfaces: dict[str, str] = {}
    out = {"interfaces": {"core.py": 'def f() -> int:\n    """Return one."""\n    total = 0\n    for i in range(3):\n        total += i\n    return total\n'}}
    assert orch._replan_interfaces(h, out, ["core.py"], interfaces, {}) == ["core.py"]
    assert "total" not in seen["core.py"] and "..." in seen["core.py"] and interfaces["core.py"] == seen["core.py"]


def test_a_replanned_task_that_waited_reads_the_findings_of_its_vertex_again_when_it_starts(tmp_path: Path):
    """§XXXVII.7: `R1_1` started with the hang found before `R1_2` had changed `environment.py`."""
    orch, h = _planned(tmp_path)
    h.vertices["core.py"].state = FAILED
    h.vertices["core.py"].history[:] = [{"task_id": "T2", "issues": ["Pytest failure: OLD hang"]}]
    _answer(orch, [{"target_node": "core.py", "description": "rewrite", "assigned_agent": "seed_coder"}])
    state = _state([])
    task = orch._replan_failed(state)["tasks"][0]
    assert "OLD hang" in task["description"]
    task["force_ready"] = True  # it starts although its dependencies are not ready: what is read is the history at that moment
    state.tasks.append(task)
    h.vertices["core.py"].history[:] = [{"task_id": "R1_2_FIX1", "issues": ["Pytest failure: NEW assertion"]}]
    h.vertices["core.py"].state = "stale"
    _idx, started = next(iter(orch._task_order(state)))
    assert "NEW assertion" in started["description"] and "OLD hang" not in started["description"] and started["description"].startswith("rewrite")


def test_the_planner_gets_open_tasks_interfaces_of_the_others_and_each_error_once(tmp_path: Path):
    """§XXXVIII.2 / P1: `task_planner` read 89k characters: the whole finished queue, every interface twice, the last error three times."""
    orch, h = _planned(tmp_path)
    h.vertices["core.py"].state = FAILED
    h.vertices["core.py"].history[:] = [
        {"task_id": "T2", "issues": ["Pytest failure: FIRST"]},
        {"task_id": "T2_FIX1", "issues": ["Pytest failure: LAST"]},
    ]
    done = {**_TASKS[0], "status": "DONE"}
    open_task = {**_TASKS[2], "status": "WAITING", "planned_description": "x"}
    sent = _answer(orch, [])
    orch._replan_failed(_state([done, open_task]))
    plan, dossier = sent[0]["current_plan"], sent[0]["repair_dossier"]["failed"][0]
    assert [t["task_id"] for t in plan["tasks"]] == [open_task["task_id"]] and "planned_description" not in plan["tasks"][0]
    assert "core.py" not in plan["interfaces"]  # it is the dossier's `planned_interface`
    assert dossier["latest_errors"] == ["Pytest failure: LAST"]
    assert [e["issues"] for e in dossier["history"]] == [["Pytest failure: FIRST"]]  # the last verdict is not repeated
    h.vertices["core.py"].state = "verified"
    h.vertices["thesis.md#ch1"] = type(h.vertices["core.py"])("thesis.md#ch1", "chapter", None, state=FAILED)
    sent_chapters = _answer(orch, [])
    orch._replan_failed(_state([]))
    assert sent_chapters[-1]["current_plan"]["interfaces"] == {}  # only a chapter failed
