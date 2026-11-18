"""Audit VIII §X (2026-11-18): one hypergraph. H is the only record of the project's structure: the plan sets the
minimum, what the agents add is recorded in H, every task target, scope, culprit and agent context is read from it,
and the plan changes during a run only in a controlled way (Audit VII B4)."""

from __future__ import annotations

import json
from pathlib import Path

from adk.hypergraph import load
from adk.hypergraph.oracles import run_fingerprint
from tests._plans import with_plan
from tests.test_root_causes_1115 import _orch

_CONFIG = '"""Config."""\nSEED: int = 1\n'
_GAME = (
    '"""Game."""\nfrom config import SEED\n\n\n'
    "def play(seed: int) -> int:\n"
    '    """Score of one game.\n\n    >>> play(0) >= 0\n    True\n    """\n'
)
_RUN = '"""Run."""\nfrom game import play\n\n\ndef main() -> None:\n    """Run the experiment."""\n'
_GAME_IMPL = _GAME.replace('    """\n', '    """\n    return seed % 3\n', 1)


def _planned(tmp_path: Path, chapters: list[dict] | None = None):
    orch = _orch(tmp_path)
    tasks = [{"task_id": "T3", "target_node": "tests/test_game.py", "description": "tests", "assigned_agent": "seed_tester"}]
    h = with_plan(orch, {"config.py": _CONFIG, "game.py": _GAME, "run.py": _RUN}, "run.py:main", tasks, chapters)
    for rel, src in (("config.py", _CONFIG), ("game.py", _GAME_IMPL), ("run.py", _RUN.replace('"""Run the experiment."""', '"""Run the experiment."""\n    play(0)'))):
        (orch.workspace_dir / rel).write_text(src, encoding="utf-8")
    return orch, h


def test_no_other_graph_file_exists():
    """The repository seed and the code know one graph file: `state/hypergraph.json`."""
    assert not (Path("adk") / "state" / "hypergraph_matrix.json").exists()
    for module in ("hypergraph_sync", "import_sync"):
        assert not (Path("adk") / "tools" / "building" / f"{module}.py").exists()
    assert not (Path("adk") / "tools" / "planning" / "blast_radius.py").exists()


def test_the_experiment_bag_holds_every_module_it_runs(tmp_path: Path):
    """A change to the method makes the results stale, not only a change to the entrypoint (2026-11-17)."""
    orch, h = _planned(tmp_path)
    assert h.edges["R:run"].members == {"run.py": "P", "results.csv": "O", "game.py": "C", "config.py": "C"}
    before = run_fingerprint(orch.workspace_dir, h)
    (orch.workspace_dir / "game.py").write_text(_GAME_IMPL.replace("seed % 3", "seed % 4"), encoding="utf-8")
    assert run_fingerprint(orch.workspace_dir, h) != before


def test_additions_are_recorded_in_h_and_promises_still_hold(tmp_path: Path):
    """A helper file imported by its module, an extra optional parameter and a public helper are accepted and the
    helper becomes part of the module's vertex; a planned parameter removed is still refused."""
    import pytest

    from adk.orchestration.common import MaterializationError

    orch, _ = _planned(tmp_path)
    helper = "def _rules(seed: int) -> int:\n    return seed % 3\n"
    game = _GAME.replace("def play(seed: int) -> int:", "def play(seed: int, verbose: bool = False) -> int:").replace(
        "from config import SEED", "from config import SEED\nfrom game_rules import _rules"
    ).replace('    """\n', '    """\n    return _rules(seed)\n', 1) + "\n\ndef board_to_str(board: list) -> str:\n    return str(board)\n"
    orch._materialize_workspace_artifact(
        "game.py", {"files": [{"filename": "game_rules.py", "content": helper}, {"filename": "game.py", "content": game}]},
        writer={"agent": "seed_coder", "task_id": "T2"},
    )
    h = load(orch.hypergraph_path)
    assert h.vertices["game.py"].files == ["game_rules.py"]
    assert h.owner_of("game_rules.py") == "game.py"
    assert h.vertices["game.py"].last_writer == {"agent": "seed_coder", "task_id": "T2"}

    with pytest.raises(MaterializationError, match="API_SIGNATURE"):
        orch._materialize_workspace_artifact(
            "game.py", {"files": [{"filename": "game.py", "content": game.replace("def play(seed: int, ", "def play(")}]}
        )


def test_an_unplanned_test_of_a_planned_module_joins_its_bag(tmp_path: Path):
    orch, _ = _planned(tmp_path)
    test = "from config import SEED\n\n\ndef test_seed() -> None:\n    assert SEED == 1\n"
    orch._materialize_workspace_artifact("tests/test_config.py", {"files": [{"filename": "tests/test_config.py", "content": test}]})
    h = load(orch.hypergraph_path)
    assert h.edges["I:config.py"].members["tests/test_config.py"] == "T"
    assert h.tested_module("tests/test_config.py") == "config.py"


def test_a_chapter_pointer_makes_the_cited_module_a_member_of_its_bag(tmp_path: Path):
    orch, _ = _planned(tmp_path, [{"index": 3, "title": "Metoda", "focus": "algorytm"}])
    thesis = "## Rozdział 3: Metoda\n\nGra: \\ref_ast{game.py:play}.\n"
    orch._materialize_workspace_artifact("thesis.md", {"files": [{"filename": "thesis.md", "content": thesis}]})
    edge = load(orch.hypergraph_path).edges["N:thesis.md#ch3"]
    assert edge.members.get("game.py") == "C" and edge.observed == ["game.py"]
    orch._materialize_workspace_artifact("thesis.md", {"files": [{"filename": "thesis.md", "content": "## Rozdział 3: Metoda\n\nBez wskaźników.\n"}]})
    assert "game.py" not in load(orch.hypergraph_path).edges["N:thesis.md#ch3"].members


# --- controlled change of the plan (Audit VII B4) -------------------------------------------------------------------

_MISMATCH = "BEHAVIOUR_MISMATCH [game.py]: the implementation does not give the results the interface specifies"


def _with_repeated_breach(orch) -> None:
    orch._remember_verdict("game.py", "T2", [_MISMATCH])
    orch._remember_verdict("game.py", "T2_FIX1", [_MISMATCH])


def _planner_answers(orch, answer: dict) -> list[dict]:
    seen: list[dict] = []

    def agent(md, payload, **_kw):
        assert Path(md).name == "plan_change_guard.md"
        seen.append(payload)
        return {"status": "ok", "output": answer}

    orch._call_agent = agent
    return seen


def test_a_breach_seen_once_does_not_reach_the_planner(tmp_path: Path):
    orch, _ = _planned(tmp_path)
    orch._remember_verdict("game.py", "T2", [_MISMATCH])
    seen = _planner_answers(orch, {"decision": "KEEP", "reason": "x"})
    assert orch._amend_spec_if_wrong("game.py", [_MISMATCH], "T2") is False and seen == []


def test_a_repeated_breach_lets_the_planner_amend_the_interface(tmp_path: Path):
    orch, _ = _planned(tmp_path)
    _with_repeated_breach(orch)
    fixed = _GAME.replace("play(0) >= 0", "play(1) == 1")
    seen = _planner_answers(orch, {"decision": "AMEND", "reason": "the example was wrong", "interface": fixed})

    assert orch._amend_spec_if_wrong("game.py", [_MISMATCH], "T2_FIX1") is True
    assert seen[0]["module"] == "game.py" and seen[0]["used_by"] == {"run.py": ["play"]}
    h = load(orch.hypergraph_path)
    assert any("play(1) == 1" in b for b in h.edges["I:game.py"].spec["behaviour"])
    assert json.loads(orch.blueprint_path.read_text(encoding="utf-8"))["interfaces"]["game.py"] == fixed
    assert "amended" in h.vertices["game.py"].history[-1]["issues"][0]


def test_an_amendment_that_removes_a_used_name_is_refused(tmp_path: Path):
    orch, _ = _planned(tmp_path)
    _with_repeated_breach(orch)
    renamed = _GAME.replace("def play(", "def run_game(").replace("play(0)", "run_game(0)")
    _planner_answers(orch, {"decision": "AMEND", "reason": "rename", "interface": renamed})

    assert orch._amend_spec_if_wrong("game.py", [_MISMATCH], "T2_FIX1") is False
    assert "play" in load(orch.hypergraph_path).edges["I:game.py"].spec["symbols"]


def test_keep_tells_the_next_attempt_why_the_interface_stands(tmp_path: Path):
    orch, _ = _planned(tmp_path)
    _with_repeated_breach(orch)
    _planner_answers(orch, {"decision": "KEEP", "reason": "play must return a non-negative score"})

    assert orch._amend_spec_if_wrong("game.py", [_MISMATCH], "T2_FIX1") is False
    assert "kept by the planner: play must return" in load(orch.hypergraph_path).vertices["game.py"].history[-1]["issues"][0]


def test_amendments_per_module_are_bounded(tmp_path: Path):
    from adk.orchestration.plan_change import AMENDMENTS_PER_MODULE

    orch, _ = _planned(tmp_path)
    seen = _planner_answers(orch, {"decision": "KEEP", "reason": "x"})
    for i in range(AMENDMENTS_PER_MODULE + 2):
        _with_repeated_breach(orch)
        orch._amend_spec_if_wrong("game.py", [_MISMATCH], f"T{i}")
    assert len(seen) == AMENDMENTS_PER_MODULE


# --- found on the mock benchmark run of 2026-11-18 ----------------------------------------------------------------


def test_a_thesis_task_naming_no_single_chapter_updates_every_chapter_it_wrote(tmp_path: Path):
    chapters = [{"index": 1, "title": "Wstęp", "focus": "cel"}, {"index": 2, "title": "Stan wiedzy", "focus": "lit"}]
    orch, _ = _planned(tmp_path, chapters)
    (orch.workspace_dir / "thesis.md").write_text("## Rozdział 1: Wstęp\n\nTekst.\n", encoding="utf-8")
    orch._on_task_result({"task_id": "T5", "target_node": "thesis.md", "description": "Author all chapters"}, passed=True)
    h = load(orch.hypergraph_path)
    assert h.vertices["thesis.md#ch1"].state == "verified" and h.vertices["thesis.md#ch2"].state == "spec"


def test_the_bibliography_written_in_a_thesis_task_is_not_off_target(tmp_path: Path):
    orch, _ = _planned(tmp_path, [{"index": 1, "title": "Wstęp", "focus": "cel"}])
    orch._materialize_workspace_artifact(
        "thesis.md",
        {"files": [{"filename": "references.bib", "content": "@article{a,\n title={A}\n}\n"}, {"filename": "thesis.md", "content": "## Rozdział 1: Wstęp\n"}]},
        writer={"agent": "background_researcher", "task_id": "T1"},
    )
    events = json.loads(orch.evolution_history_path.read_text(encoding="utf-8"))["events"] if orch.evolution_history_path.exists() else []
    assert not any(e["type"] == "OFF_TARGET_WRITE" for e in events)


def test_the_experiment_does_not_run_while_a_module_it_runs_is_a_stub(tmp_path: Path):
    orch, _ = _planned(tmp_path)
    (orch.workspace_dir / "game.py").write_text(_GAME + "    raise NotImplementedError\n", encoding="utf-8")
    assert orch._experiment_still_stubbed() is True
    (orch.workspace_dir / "game.py").write_text(_GAME_IMPL, encoding="utf-8")
    assert orch._experiment_still_stubbed() is False
