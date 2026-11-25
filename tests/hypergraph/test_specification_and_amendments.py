"""The specification in force: the planned interfaces are protected from rewrites, a contract change may add but not remove what others use, a repeated breach lets the planner amend the interface (bounded) and a typo in a test is no gap."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adk.hypergraph import load
from adk.mocks import code_fixtures as fx
from adk.orchestration.common import MaterializationError
from adk.orchestration.failure_kinds import HARNESS_ENFORCED_CATEGORIES, _issue_category
from adk.orchestration.plan_change import _typos
from tests.support.failed_vertex_project import _planned
from tests.support.game_project import (
    _GAME,
    _MISMATCH,
    _planner_answers,
    _with_repeated_breach,
)
from tests.support.game_project import _planned as _planned_game_project
from tests.support.sample_research_project import _CONFIG, _spec_orch


def test_rewriting_the_planned_config_into_getters_is_rejected(tmp_path: Path):
    """X4, 02: T3 rewrote config constants into get_channels() and the getters became the contract."""
    orch = _spec_orch(tmp_path)
    before = (orch.workspace_dir / "src/config.py").read_text(encoding="utf-8")
    getters = {"files": [{"filename": "src/config.py", "content": 'def get_channels() -> list[str]:\n    return ["EEG"]\n'}]}
    with pytest.raises(MaterializationError) as exc:
        orch._materialize_workspace_artifact("src/config.py", getters)
    assert "API_MISSING" in str(exc.value) and "CHANNELS" in str(exc.value)
    assert (orch.workspace_dir / "src/config.py").read_text(encoding="utf-8") == before


def test_contract_change_cannot_remove_what_other_modules_use(tmp_path: Path):
    orch = _spec_orch(tmp_path)
    answer = {
        "files": [{"filename": "src/config.py", "content": 'def get_channels() -> list[str]:\n    return ["EEG"]\n'}],
        "contract_change": {"reason": "getters are nicer"},
    }
    with pytest.raises(MaterializationError) as exc:
        orch._materialize_workspace_artifact("src/config.py", answer)
    assert "src/data_generator.py is planned to use them" in str(exc.value)


def test_contract_change_may_add_to_the_interface(tmp_path: Path):
    orch = _spec_orch(tmp_path)
    added = _CONFIG + "TEST_SPLIT: float = 0.2\n"
    orch._materialize_workspace_artifact(
        "src/config.py", {"files": [{"filename": "src/config.py", "content": added}], "contract_change": {"reason": "split ratio"}}
    )
    assert "TEST_SPLIT" in load(orch.hypergraph_path).edges["I:src/config.py"].spec["symbols"]
    assert any('"SPEC_CHANGED"' in line for line in (orch.logger.events_path.read_text(encoding="utf-8").splitlines()))


def test_files_outside_the_plan_and_appended_public_symbols_are_rejected(tmp_path: Path):
    """X3/X4, 02: `_iforest.py` in the root and `validation.py` became nodes and contract."""
    orch = _spec_orch(tmp_path)
    with pytest.raises(MaterializationError) as exc:
        orch._materialize_workspace_artifact("_iforest.py", {"files": [{"filename": "_iforest.py", "content": "X = 1\n"}]})
    assert "FILE_OUTSIDE_PLAN" in str(exc.value)
    assert not (orch.workspace_dir / "_iforest.py").exists()


def test_breaches_of_the_specification_are_enforced_by_the_harness_not_by_rules():
    category = _issue_category(["IMPORT_OUTSIDE_SPEC [src/experiment.py]: imports N_REPETITIONS from src/config.py"])
    assert category == "spec" and category in HARNESS_ENFORCED_CATEGORIES


def test_a_breach_of_the_specification_asks_the_planner_when_it_repeats(tmp_path: Path):
    orch, _h = _planned(tmp_path)
    (orch.workspace_dir / "core.py").write_text(fx.TICTACTOE_CORE_CODE, encoding="utf-8")
    asked: list[str] = []
    orch._call_agent = lambda md, *_a, **_k: asked.append(Path(md).name) or {"status": "ok", "output": {"decision": "KEEP", "reason": "fine"}}
    breach = ["API_SIGNATURE [core.py]: train_and_evaluate(seed) is called without it"]
    orch._remember_verdict("core.py", "T2", breach)
    assert orch._amend_spec_if_wrong("core.py", breach, "T2") is False
    assert asked == []  # the first occurrence waits for a repetition
    orch._remember_verdict("core.py", "T2_FIX1", breach)
    orch._amend_spec_if_wrong("core.py", breach, "T2_FIX1")
    assert asked == ["plan_change_guard.md"]


def test_a_test_typo_is_not_an_interface_gap() -> None:
    """E3: `no_std` read by a test became an alias of `noise_std` in the interface."""
    interface = "class SyntheticDataset:\n    def __init__(self, noise_std: float) -> None:\n        self.noise_std = noise_std\n"
    issue = ("TEST_OUTSIDE_SPEC [tests/test_data.py]: reads SyntheticDataset.no_std, which the interface does not "
             "declare (test only declared methods and attributes)")
    assert _typos([issue], interface) == ["SyntheticDataset.no_std (did you mean `noise_std`?)"]
    assert _typos([issue.replace("no_std", "colour")], interface) == []


def test_a_breach_seen_once_does_not_reach_the_planner(tmp_path: Path):
    orch, _ = _planned_game_project(tmp_path)
    orch._remember_verdict("game.py", "T2", [_MISMATCH])
    seen = _planner_answers(orch, {"decision": "KEEP", "reason": "x"})
    assert orch._amend_spec_if_wrong("game.py", [_MISMATCH], "T2") is False and seen == []


def test_a_repeated_breach_lets_the_planner_amend_the_interface(tmp_path: Path):
    orch, _ = _planned_game_project(tmp_path)
    _with_repeated_breach(orch)
    fixed = _GAME.replace("never negative", "between 0 and 2")
    seen = _planner_answers(orch, {"decision": "AMEND", "reason": "the example was wrong", "interface": fixed})

    assert orch._amend_spec_if_wrong("game.py", [_MISMATCH], "T2_FIX1") is True
    assert seen[0]["module"] == "game.py" and seen[0]["used_by"] == {"run.py": ["play"]}
    h = load(orch.hypergraph_path)
    assert "between 0 and 2" in json.loads(orch.blueprint_path.read_text(encoding="utf-8"))["interfaces"]["game.py"]
    assert json.loads(orch.blueprint_path.read_text(encoding="utf-8"))["interfaces"]["game.py"] == fixed
    assert "amended" in h.vertices["game.py"].history[-1]["issues"][0]


def test_an_amendment_that_removes_a_used_name_is_refused(tmp_path: Path):
    orch, _ = _planned_game_project(tmp_path)
    _with_repeated_breach(orch)
    renamed = _GAME.replace("def play(", "def run_game(").replace("play(0)", "run_game(0)")
    _planner_answers(orch, {"decision": "AMEND", "reason": "rename", "interface": renamed})

    assert orch._amend_spec_if_wrong("game.py", [_MISMATCH], "T2_FIX1") is False
    assert "play" in load(orch.hypergraph_path).edges["I:game.py"].spec["symbols"]


def test_keep_tells_the_next_attempt_why_the_interface_stands(tmp_path: Path):
    orch, _ = _planned_game_project(tmp_path)
    _with_repeated_breach(orch)
    _planner_answers(orch, {"decision": "KEEP", "reason": "play must return a non-negative score"})

    assert orch._amend_spec_if_wrong("game.py", [_MISMATCH], "T2_FIX1") is False
    assert "kept by the planner: play must return" in load(orch.hypergraph_path).vertices["game.py"].history[-1]["issues"][0]


def test_amendments_per_module_are_bounded(tmp_path: Path):
    from adk.orchestration.plan_change import AMENDMENTS_PER_MODULE

    orch, _ = _planned_game_project(tmp_path)
    seen = _planner_answers(orch, {"decision": "KEEP", "reason": "x"})
    for i in range(AMENDMENTS_PER_MODULE + 2):
        _with_repeated_breach(orch)
        orch._amend_spec_if_wrong("game.py", [_MISMATCH], f"T{i}")
    assert len(seen) == AMENDMENTS_PER_MODULE
