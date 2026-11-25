"""The structure of H, the one hypergraph: the experiment bag holds every module it runs, additions are recorded, an unplanned test joins the bag of its module, chapters and the bibliography belong to the right bags and a diff finds broken promises."""

from __future__ import annotations

import json
from pathlib import Path

from adk.hypergraph import diff, load, observe
from adk.hypergraph.oracles import run_fingerprint
from tests.support.game_project import _GAME, _GAME_IMPL, _planned
from tests.support.sample_research_project import (
    _EXPERIMENT_IFACE,
    _GENERATOR,
    _GOOD,
    _h,
)


def test_build_gives_typed_bags_roles_and_order():
    h, problems = _h()
    assert problems == []
    assert h.edges["I:src/config.py"].members == {"src/config.py": "P", "src/data_generator.py": "C", "src/experiment.py": "C"}
    assert h.edges["I:src/data_generator.py"].members["tests/test_data_generator.py"] == "T"
    # R holds every module the experiment runs (Audit VIII): a change to any of them makes the results stale.
    assert h.edges["R:run"].members == {
        "src/experiment.py": "P", "results.csv": "O", "src/config.py": "C", "src/data_generator.py": "C"
    }
    assert ("R:run", "N:thesis.md#ch4") in h.order and ("R:run", "N:thesis.md#ch1") not in h.order
    assert h.vertices["src/experiment.py"].kind == "entry" and h.vertices["src/config.py"].state == "stub"


def test_diff_finds_broken_promises_and_files_outside_the_plan(tmp_path: Path):
    """X3/X4 as seen by H_obs − H: getters instead of the planned constants (a broken promise), `_iforest.py` that
    no planned module imports. An appended public `fit` is an addition, allowed since Audit VIII (§X)."""
    h, _ = _h()
    ws = tmp_path / "ws"
    for rel, source in _GOOD.items():
        (ws / rel).parent.mkdir(parents=True, exist_ok=True)
        (ws / rel).write_text(source, encoding="utf-8")
    assert diff(h, observe(ws)) == []
    (ws / "src/experiment.py").write_text(_EXPERIMENT_IFACE + "\n\ndef fit(self, samples):\n    pass\n", encoding="utf-8")
    (ws / "src/config.py").write_text('def get_channels() -> list[str]:\n    return ["EEG"]\n', encoding="utf-8")
    (ws / "_iforest.py").write_text("X = 1\n", encoding="utf-8")
    found = {(v.rule, v.culprit) for v in diff(h, observe(ws))}
    assert not any(culprit == "src/experiment.py" for _rule, culprit in found)
    assert ("API_MISSING", "src/config.py") in found
    assert ("FILE_OUTSIDE_PLAN", "_iforest.py") in found
    # A helper the planned module imports is part of that module, not a file outside the plan.
    (ws / "src/_math.py").write_text("def _mean(xs):\n    return sum(xs) / len(xs)\n", encoding="utf-8")
    (ws / "src/data_generator.py").write_text(_GENERATOR.replace("from src.config", "from src._math import _mean\nfrom src.config"), encoding="utf-8")
    assert not any(culprit == "src/_math.py" for _rule, culprit in {(v.rule, v.culprit) for v in diff(h, observe(ws))})


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
