"""§XIV: the plan critic does not block on guessed doctest results; repairs blame the unverified one of a
test/module pair and stop when the author's repair leaves the very same error."""

from __future__ import annotations

from pathlib import Path

from adk.mocks import code_fixtures as fx
from adk.orchestration import repair
from adk.orchestration.common import _RunState
from adk.orchestration.failure_attribution import _suspect_test
from tests.test_audit_xi import _events, _planned, _seen
from tests.test_plan_spec_validation import _base_plan, _make_orch


def test_a_guessed_doctest_result_is_a_warning_not_a_blocker(tmp_path: Path) -> None:
    """Q1: about half of the critic's blockers in 02/03 predicted what an example returns ("float is fragile",
    "might block paths"); the harness checks every example on the code itself."""
    orch = _make_orch(tmp_path)
    planner_calls: list[dict] = []

    def agents(md, payload, **_kw):
        if Path(md).name == "plan_critic_guard.md":
            return {"status": "ok", "output": {"status": "FAIL", "issues": [
                {"blocking": True, "category": "doctest", "where": "src/mod_a.py",
                 "problem": "helper_a() may return a float that rounds differently", "fix": "round the example"},
            ]}}
        planner_calls.append(payload)
        return {"status": "ok", "output": {}}

    orch._call_agent = agents
    _, _, blockers = orch._validated_plan(_base_plan(), {"user_prompt": "p"}, tmp_path / "planner.md")
    assert blockers == [] and planner_calls == []


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
    assert len(built) == 1  # one fast repair, not FAST_REPAIR_ATTEMPTS
    assert [e["event"] for e in _events(orch, seen) if e["event"] == "REPAIR_SAME_ERROR"] == ["REPAIR_SAME_ERROR"]
