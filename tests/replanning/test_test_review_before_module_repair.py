"""The review of a test before its module is repaired again: when a test is reviewed, by whom, once and without costing a repair attempt, and when a changed interface allows one more review."""

from __future__ import annotations

from pathlib import Path

from adk.mocks import code_fixtures as fx
from adk.orchestration.recovery import repair
from adk.orchestration.common import _RunState
from adk.orchestration.verification.attribution import _suspect_test
from tests.support.failed_vertex_project import _TASKS, _events, _planned, _seen
from tests.support.queue_state import _state

_PYTEST_ON_TEST = "Pytest failure:\ntests\\test_core.py:40: in test_x\ncore.py:88: in f\nE IndexError: boom"


def _blamed_twice(h) -> None:
    h.vertices["core.py"].history[:] = [{"task_id": "T3", "issues": [_PYTEST_ON_TEST]}, {"task_id": "T3", "issues": [_PYTEST_ON_TEST]}]


def _blamed_once(h) -> None:
    h.vertices["core.py"].history[:] = [{"task_id": "T3", "issues": [_PYTEST_ON_TEST]}]


def _repair_with(tmp_path: Path, max_retries: int):
    orch, h = _planned(tmp_path)
    _blamed_twice(h)
    built: list[dict] = []
    orch._execute_builder_step = lambda task, **_k: built.append(task)
    orch._refresh_experiment_after_code = lambda *_a, **_k: None
    orch._amend_spec_if_wrong = lambda *_a, **_k: False
    failing = {"status": "FAIL", "failed_file": "core.py", "failed_agent": "seed_coder", "issues": [_PYTEST_ON_TEST], "errors": []}
    orch._run_verification_step = lambda *_a, **_k: dict(failing)
    task = {**_TASKS[1]}
    state = _state([task])
    state.max_retries = max_retries
    orch._repair_task(state, task, dict(failing), "core.py", "core.py")
    return orch, built, task


def test_a_fresh_test_against_a_verified_module_is_the_suspect(tmp_path: Path) -> None:
    """Q2 (R1): 01 blamed the correct ttt_agent.py for a test asserting `0.1 > 0.5`; six repairs followed."""
    _orch, h = _planned(tmp_path)
    test = next(rel for rel in h.vertices if rel.startswith("tests/"))
    module = h.tested_module(test)
    h.vertices[module].state, h.vertices[test].state = "verified", "written"
    assert _suspect_test(h, module, test)
    h.vertices[module].state = "impl"  # the module changed after its verification: it is the suspect again
    assert not _suspect_test(h, module, test)
    h.vertices[module].state, h.vertices[test].state = "verified", "verified"  # both checked: the code broke it
    assert not _suspect_test(h, module, test)


def test_the_same_error_after_a_repair_ends_the_fast_repairs(tmp_path: Path) -> None:
    """Q3: 01 T1 and T2 got the identical error three times each; the author is not the one to fix it."""
    orch, _h = _planned(tmp_path)
    (orch.workspace_dir / "core.py").write_text(fx.TICTACTOE_CORE_CODE, encoding="utf-8")
    built: list[dict] = []
    orch._execute_builder_step = lambda task, **_k: built.append(task)
    orch._refresh_experiment_after_code = lambda *_a, **_k: None
    orch._amend_spec_if_wrong = lambda *_a, **_k: False
    failing = {"status": "FAIL", "failed_file": "core.py", "failed_agent": "seed_coder",
               "issues": ["Ruff lint failure: core.py:12:5: F821 Undefined name `x`"], "errors": []}
    orch._run_verification_step = lambda *_a, **_k: dict(failing)
    task = {"task_id": "T2", "target_node": "core.py", "description": "Implement core.py", "assigned_agent": "seed_coder"}
    state = _RunState(user_prompt="p", max_retries=repair.FAST_REPAIR_ATTEMPTS + 1, multi_cycle_waves=True, tasks=[task])
    seen = _seen(orch)
    orch._repair_task(state, task, dict(failing), "core.py", "core.py")
    assert len(built) == 2  # §XXVII: a vertex of H gets both author attempts (the shortcut led to `O7`, i.e. one)
    assert not [e for e in _events(orch, seen) if e["event"] == "REPAIR_SAME_ERROR"]


def test_the_same_breach_of_the_specification_does_not_skip_the_planner(tmp_path: Path) -> None:
    """A repeated API_* breach may be the plan's fault: the shortcut to the full cycle used to end the fast repairs
    before `_amend_spec_if_wrong` could judge the interface on the next attempt."""
    orch, _h = _planned(tmp_path)
    (orch.workspace_dir / "core.py").write_text(fx.TICTACTOE_CORE_CODE, encoding="utf-8")
    built: list[dict] = []
    judged: list[str] = []
    orch._execute_builder_step = lambda task, **_k: built.append(task)
    orch._refresh_experiment_after_code = lambda *_a, **_k: None
    orch._amend_spec_if_wrong = lambda failed_file, *_a, **_k: judged.append(failed_file) or False
    failing = {"status": "FAIL", "failed_file": "core.py", "failed_agent": "seed_coder",
               "issues": ["API_SIGNATURE [core.py]: train_and_evaluate(seed) is called without it"], "errors": []}
    orch._run_verification_step = lambda *_a, **_k: dict(failing)
    task = {"task_id": "T2", "target_node": "core.py", "description": "Implement core.py", "assigned_agent": "seed_coder"}
    state = _RunState(user_prompt="p", max_retries=repair.FAST_REPAIR_ATTEMPTS + 1, multi_cycle_waves=True, tasks=[task])
    seen = _seen(orch)
    orch._repair_task(state, task, dict(failing), "core.py", "core.py")
    assert len(built) == repair.FAST_REPAIR_ATTEMPTS and judged == ["core.py"] * repair.FAST_REPAIR_ATTEMPTS
    assert [e for e in _events(orch, seen) if e["event"] == "REPAIR_SAME_ERROR"] == []


def test_a_test_is_reviewed_after_the_module_failed_on_it(tmp_path: Path):
    from adk.orchestration.verification.attribution import _test_to_review

    _orch_, h = _planned(tmp_path)
    assert _test_to_review(h, "core.py", set()) is None  # no failures yet
    _blamed_once(h)
    assert _test_to_review(h, "core.py", set()) == "tests/test_core.py"
    assert _test_to_review(h, "core.py", {("core.py", "tests/test_core.py")}) is None  # once per pair
    h.vertices["tests/test_core.py"].state = "verified"
    assert _test_to_review(h, "core.py", set()) is None  # a test that passed is not suspected
    h.vertices["tests/test_core.py"].state = "written"
    h.vertices["core.py"].history[0] = {"task_id": "T3", "issues": ["Ruff lint failure: core.py:1:1: F821 x"]}
    assert _test_to_review(h, "core.py", set()) is None  # failures of another kind do not count


def test_the_review_goes_to_the_author_of_the_test_once_and_costs_no_repair_attempt(tmp_path: Path):
    orch, built, task = _repair_with(tmp_path, max_retries=2)
    assert [b["target_node"] for b in built] == ["tests/test_core.py", "core.py", "core.py"]
    assert "check the test, not the module" in built[0]["description"] and "check the test" not in built[1]["description"]
    assert task["repair_attempts"] == 2  # the module's first repair came after the review as attempt 1 (the review took none)
    assert orch._reviewed_tests == {("core.py", "tests/test_core.py")}


def test_a_verified_test_is_reviewed_only_after_the_interface_of_its_module_changed(tmp_path: Path):
    from adk.orchestration.verification.attribution import _test_to_review

    orch, h = _planned(tmp_path)
    _blamed_once(h)
    h.vertices["tests/test_core.py"].state = "verified"
    assert _test_to_review(h, "core.py", set()) is None
    orch._reopen_test_review(h, "core.py")
    assert orch._pending_review == {("core.py", "tests/test_core.py")}
    assert _test_to_review(h, "core.py", orch._reviewed_tests, orch._pending_review) == "tests/test_core.py"


def test_a_changed_interface_allows_one_more_review_of_the_same_test(tmp_path: Path):
    from adk.orchestration.verification.attribution import _test_to_review

    orch, h = _planned(tmp_path)
    _blamed_once(h)
    pair = ("core.py", "tests/test_core.py")
    orch._reviewed_tests = {pair}
    assert _test_to_review(h, "core.py", orch._reviewed_tests) is None  # reviewed for this version of σ
    orch._reopen_test_review(h, "core.py")  # σ changed (SPEC_AMENDED)
    assert pair not in orch._reviewed_tests
    assert _test_to_review(h, "core.py", orch._reviewed_tests, orch._pending_review) == "tests/test_core.py"


def test_only_a_change_of_the_call_contract_counts_as_a_change_of_the_interface():
    from adk.orchestration.planning.change import _contract_changed

    old = 'def f(x: int) -> tuple[int, int]:\n    """Old."""\n    ...\n'
    docs = 'def f(x: int) -> tuple[int, int]:\n    """New words."""\n    ...\n'
    returns = 'def f(x: int) -> int:\n    """Old."""\n    ...\n'
    spec = {"symbols": {"f": {"kind": "func", "params": ["x"], "required": ["x"]}}}
    assert not _contract_changed(spec, spec, old, docs)
    assert _contract_changed(spec, spec, old, returns)
    assert _contract_changed(spec, {"symbols": {}}, old, old)


def test_a_review_that_changes_nothing_sends_the_next_repair_to_the_module(tmp_path: Path):
    orch, h = _planned(tmp_path)
    _blamed_once(h)
    built: list[dict] = []

    def _builder(task, **_k):
        built.append(task)
        if task["target_node"].startswith("tests/"):
            raise RuntimeError("the answer changes nothing")

    orch._execute_builder_step = _builder
    orch._refresh_experiment_after_code = lambda *_a, **_k: None
    orch._amend_spec_if_wrong = lambda *_a, **_k: False
    failing = {"status": "FAIL", "failed_file": "core.py", "failed_agent": "seed_coder", "issues": [_PYTEST_ON_TEST], "errors": []}
    orch._run_verification_step = lambda *_a, **_k: dict(failing)
    task = {**_TASKS[1]}
    state = _state([task])
    state.max_retries = 2
    orch._repair_task(state, task, dict(failing), "core.py", "core.py")
    assert [b["target_node"] for b in built] == ["tests/test_core.py", "core.py", "core.py"]  # the review took no attempt, the module follows
    assert orch._reviewed_tests == {("core.py", "tests/test_core.py")}


def test_a_test_of_another_module_named_in_the_failures_is_reviewed_too(tmp_path: Path):
    from adk.orchestration.verification.attribution import _test_to_review

    _orch_, h = _planned(tmp_path)
    foreign = "Pytest failure:\ntests\\test_other.py:5: in test_y\ncore.py:9: in f\nE TypeError: unhashable"
    h.vertices["core.py"].history[:] = [{"task_id": "T3", "issues": [foreign]}]
    from adk.hypergraph.model import Vertex

    h.vertices["tests/test_other.py"] = Vertex(id="tests/test_other.py", kind="test", owner=None, state="written")
    assert _test_to_review(h, "core.py", set()) == "tests/test_other.py"
    h.vertices["tests/test_other.py"].state = "verified"
    assert _test_to_review(h, "core.py", set()) is None
