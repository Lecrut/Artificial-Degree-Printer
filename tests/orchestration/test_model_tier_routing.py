"""Which model works: the small one by default, the large one after failures counted on the vertex, later for documents, longer for mechanical failures, planning tiers, and what counts as a failure."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from adk.mocks import code_fixtures as fx
from adk.mocks.scenarios import config_source
from adk.orchestration.common import MaterializationError
from adk.orchestration.failure_kinds import is_mechanical_failure
from adk.tools.planning import select_model_tier, select_planning_tier
from tests.support.failed_vertex_project import _planned, _repair_once
from tests.support.game_project import (
    _GAME,
    _MISMATCH,
    _planner_answers,
    _with_repeated_breach,
)
from tests.support.game_project import _planned as _planned_game
from tests.support.staged_planning import _base_plan, _critic_fail, _make_orch, _run


def _builder_with_rejections(tmp_path: Path, rejections: int) -> tuple[Any, Any]:
    orch, h = _planned(tmp_path)
    (orch.workspace_dir / "config.py").write_text(config_source(fx.TICTACTOE_CONFIG_AST_NODES), encoding="utf-8")
    left = {"n": rejections}

    def materialize(*_a: Any, **_k: Any) -> None:
        if left["n"] > 0:
            left["n"] -= 1
            raise MaterializationError("the answer has the wrong shape")

    orch._materialize_workspace_artifact = materialize
    orch._call_agent = lambda *_a, **_k: {"status": "ok", "output": {}}
    return orch, h


def test_the_large_model_takes_over_a_vertex_after_its_second_failure(tmp_path: Path):
    logic = "Pytest failure: FAILED tests/test_core.py::test_winner - AssertionError: assert 'X' == 'O'"
    _task, tier = _repair_once(tmp_path, failures=2, issue=logic)
    assert tier == "LRM"


def test_a_mechanical_failure_stays_with_the_small_model_longer(tmp_path: Path):
    """§XXIX D6: `F821` names its line and its fix, so a vertex that failed twice on it is still the small model's."""
    assert _repair_once(tmp_path / "second", failures=2)[1] == "SML"
    assert _repair_once(tmp_path / "fourth", failures=4)[1] == "LRM"


def test_failures_are_counted_on_the_vertex_across_tasks(tmp_path: Path):
    orch, h = _planned(tmp_path)
    orch._remember_verdict("core.py", "T2", ["pytest failed in tests/test_core.py: x"])
    orch._remember_verdict("core.py", "Q1_FIX_core_2", ["ANSWER_REJECTED: y"])
    assert h.vertices["core.py"].failures == 2 and orch._vertex_failures("core.py") == 2


def test_complexity_router_follows_the_attempt():
    # The tier follows the attempt, not the node: the small model works, the large one steps in after two failures.
    assert select_model_tier() == "SML"
    assert select_model_tier(failures=1) == "SML"
    assert select_model_tier(failures=2) == "LRM"


def test_the_small_model_does_the_first_answer_of_a_module_author_and_the_large_one_all_the_rest() -> None:
    assert select_planning_tier("plan_module") == "SML"
    assert select_planning_tier("plan_module", attempt=2) == "LRM" and select_planning_tier("plan_module", has_feedback=True) == "LRM"
    for agent in ("plan_outline", "module_critic_guard", "plan_critic_guard", "task_planner"):
        assert select_planning_tier(agent) == "LRM", agent


def test_a_module_is_designed_on_the_small_model_and_corrected_on_the_large_one(tmp_path: Path) -> None:
    orch = _make_orch(tmp_path)
    seen: list[tuple[str, str | None, str]] = []
    original = orch._call_planning_agent

    def spy(md: Any, payload: dict, **kw: Any) -> dict:
        seen.append((Path(md).stem, (payload.get("module") or {}).get("file"), kw.get("model_tier", "LRM")))
        return original(md, payload, **kw)

    orch._call_planning_agent = spy
    critic = lambda payload, _n: _critic_fail("src/mod_a.py:helper_a") if payload["module"]["file"] == "src/mod_a.py" else None  # noqa: E731
    (_, _, blockers), _calls = _run(orch, _base_plan(), {"module_critic_guard": critic})
    assert blockers == []
    assert [tier for agent, rel, tier in seen if agent == "plan_module" and rel == "src/mod_a.py"] == ["SML", "LRM"]  # a critic blocked once
    assert {tier for agent, rel, tier in seen if agent == "plan_module" and rel != "src/mod_a.py"} == {"SML"}
    assert {tier for agent, _rel, tier in seen if agent != "plan_module"} == {"LRM"}


def test_the_model_follows_the_vertex_its_kind_and_the_failure() -> None:
    assert [select_model_tier(f) for f in (0, 1, 2)] == ["SML", "SML", "LRM"]
    assert [select_model_tier(f, kind="chapter") for f in (2, 3)] == ["SML", "LRM"]  # a thesis chapter waits one failure longer
    assert [select_model_tier(f, kind="research") for f in (2, 3)] == ["SML", "LRM"] and select_model_tier(2, kind="test") == "LRM"
    assert [select_model_tier(f, mechanical=True) for f in (2, 3, 4)] == ["SML", "SML", "LRM"]
    assert select_model_tier(remediation=True) == "LRM" and select_model_tier(0, mechanical=True, remediation=True) == "LRM"


def test_a_failure_is_mechanical_when_every_finding_names_its_own_fix() -> None:
    ruff = "Ruff lint failure: core.py:42:5: F821 Undefined name `np`"
    assert is_mechanical_failure([ruff]) and is_mechanical_failure([ruff, "Syntax error in core.py: invalid syntax"])
    assert is_mechanical_failure(["Import error in core.py: cannot import name 'x'"])
    csv = "results.csv lacks the columns std_dev. The file has exactly the columns method,metric,value (optional std_dev,n_runs)"
    assert is_mechanical_failure([csv])
    logic = "Pytest failure: FAILED tests/test_core.py::test_winner - AssertionError: assert 'X' == 'O'"
    assert not is_mechanical_failure([logic]) and not is_mechanical_failure([ruff, logic]) and not is_mechanical_failure([])


def test_an_answer_the_retry_put_right_is_not_a_failure(tmp_path: Path) -> None:
    orch, h = _builder_with_rejections(tmp_path, rejections=1)
    orch._execute_builder_step({"task_id": "T1", "target_node": "config.py", "assigned_agent": "seed_coder"}, "SML")
    assert h.vertices["config.py"].failures == 0 and h.vertices["config.py"].history == []


def test_an_answer_rejected_twice_is_one_failure_with_its_reason_on_the_vertex(tmp_path: Path) -> None:
    orch, h = _builder_with_rejections(tmp_path, rejections=2)
    with pytest.raises(MaterializationError):
        orch._execute_builder_step({"task_id": "T1", "target_node": "config.py", "assigned_agent": "seed_coder"}, "SML")
    assert h.vertices["config.py"].failures == 1
    assert h.vertices["config.py"].history[-1]["issues"] == ["ANSWER_REJECTED: the answer has the wrong shape"]


def test_a_new_contract_starts_the_small_model_again(tmp_path: Path) -> None:
    orch, _ = _planned_game(tmp_path)
    _with_repeated_breach(orch)
    h = orch._project_h()
    tests = h.tests_of("game.py")
    for vertex in ("game.py", *tests):
        h.vertices[vertex].failures = 3
    fixed = _GAME.replace("never negative", "between 0 and 2")
    _planner_answers(orch, {"decision": "AMEND", "reason": "the example was wrong", "interface": fixed})
    assert orch._amend_spec_if_wrong("game.py", [_MISMATCH], "T2_FIX1") is True
    assert [h.vertices[v].failures for v in ("game.py", *tests)] == [0] * (1 + len(tests))
    assert h.vertices["run.py"].failures == 0 and orch._vertex_failures("game.py") == 0


def test_the_auditors_of_the_defense_run_on_the_small_model(tmp_path: Path) -> None:
    orch, _h = _planned(tmp_path)
    orch.include_docs = False
    (orch.workspace_dir / "config.py").write_text(config_source(fx.TICTACTOE_CONFIG_AST_NODES), encoding="utf-8")
    (orch.workspace_dir / "core.py").write_text(fx.TICTACTOE_CORE_CODE, encoding="utf-8")
    tiers: dict[str, str] = {}

    def agent(md: Any, *_a: Any, **kw: Any) -> dict:
        tiers[Path(md).stem] = kw.get("model_tier", "")
        return {"status": "ok", "output": {"status": "PASS", "issues": []}}

    orch._call_agent = agent
    orch._run_verification_step({"task_id": "FINAL", "target_node": "core.py"}, include_docs=False, is_final_gate=True)
    assert tiers.get("code_auditor") == "SML" and tiers.get("redteam_critic_guard") == "SML"
