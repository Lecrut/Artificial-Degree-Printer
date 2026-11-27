"""What a builder is shown when it works or repairs: the interface of the module under test in full, only the used part of its dependencies, the code of the failing tests, the symbol to fix with its line, the hint for an undefined name."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from adk.orchestration.common import available_package_imports
from adk.orchestration.findings import focus_symbols, repair_findings, symbol_sources
from tests.support.failed_vertex_project import _CONFIG as _CONFIG_failed_vertex_project
from tests.support.failed_vertex_project import _planned, _repair_once
from tests.support.orchestrator_sandbox import _orch
from tests.support.sample_research_project import _ENTRY, _spec_orch
from tests.support.tictactoe_interface import ENV_INTERFACE

def test_a_code_task_sees_its_specification_and_history_not_the_writers_grounding(tmp_path: Path):
    """X5 (no memory of earlier attempts) and U7 (writer directives in the coder's payload, `\ref_csv` in code).
    Since Audit VIII the whole project context of a task is this slice of H."""
    orch = _spec_orch(tmp_path)
    orch._remember_verdict("src/data_generator.py", "T6", ["IMPORT_OUTSIDE_SPEC: imports SEED_VALUE"])
    context = orch._context_for("src/data_generator.py", "src/data_generator.py")
    assert sorted(context["specification"]) == ["src/config.py", "src/data_generator.py"]
    assert context["specification"]["src/config.py"]["symbols"]["CHANNELS"]["kind"] == "const"
    assert context["previous_attempts"][0]["task_id"] == "T6"
    # The generator is run by the experiment: it learns the entrypoint and metrics from R, nothing else.
    assert context["experiment"]["entrypoint"] == _ENTRY
    assert not {"may_cite", "exports", "grounded_hypergraph_state", "hypergraph_nodes"} & set(context)


def test_a_ruff_finding_names_the_function_and_its_line_of_code(tmp_path: Path):
    (tmp_path / "config.py").write_text(_CONFIG_failed_vertex_project, encoding="utf-8")
    [f] = repair_findings(["Ruff lint failure: config.py:12:12: F821 Undefined name `self`\nFound 1 error."], tmp_path)
    assert (f.file, f.symbol, f.line, f.code) == ("config.py", "get_results_dir", 12, "return self.output_path")
    assert str(f) == "config.py > get_results_dir, line 12: `return self.output_path` -- F821 Undefined name `self`"
    assert focus_symbols([f], "config.py") == ["get_results_dir"]


def test_the_same_finding_is_listed_once_and_symbol_sources_read_methods(tmp_path: Path):
    (tmp_path / "config.py").write_text(_CONFIG_failed_vertex_project, encoding="utf-8")
    issue = "Ruff lint failure: config.py:12:12: F821 Undefined name `self`"
    assert len(repair_findings([issue, issue], tmp_path)) == 1
    sources = symbol_sources(tmp_path, "config.py", ["Paths.results", "get_results_dir"])
    assert sources["Paths.results"].startswith("def results(self)") and "self.output_path" in sources["get_results_dir"]


def test_a_fast_repair_names_the_broken_symbol_and_carries_its_code(tmp_path: Path):
    task, tier = _repair_once(tmp_path, failures=0)
    assert task["description"].startswith("Fix `check_winner` in core.py")
    assert task["task_context"] == "Implement core.py"
    assert task["repair_focus"]["file"] == "core.py" and task["repair_focus"]["symbols"]["check_winner"].startswith("def check_winner(")
    assert tier == "SML"


def test_an_undefined_name_gets_its_import_line_as_a_hint(tmp_path: Path) -> None:
    """F821 `pd`, `plot_results`, `src` failed six tasks after three repairs each with no hint. D2 (2026-11-14):
    the harness inserts nothing; the author gets the one import line from the source of truth."""
    from types import SimpleNamespace

    from adk.orchestration.findings import repair_findings
    from adk.orchestration.import_hints import importable_names

    edge = SimpleNamespace(type="I", id="I:src/plots.py", spec={"import": "src.plots", "symbols": {"plot_results": {"kind": "func"}}})
    h = SimpleNamespace(edges={edge.id: edge})
    source = "def run():\n    plot_results(pd)\n    src.plots.plot_results()\n    mystery()\n"
    (tmp_path / "experiment.py").write_text(source, encoding="utf-8")
    issue = (
        "Ruff lint failure: experiment.py:2:5: F821 Undefined name `plot_results`\nexperiment.py:2:18: F821 Undefined name `pd`\n"
        "experiment.py:3:5: F821 Undefined name `src`\nexperiment.py:4:5: F821 Undefined name `mystery`"
    )
    texts = [f.text for f in repair_findings([issue], tmp_path, lambda rel: importable_names(h, rel, available_package_imports()))]
    assert "`from src.plots import plot_results`" in texts[0] and "`import pandas as pd`" in texts[1]
    assert "`import src.plots`" in texts[2] and "import line" not in texts[3]
    assert (tmp_path / "experiment.py").read_text(encoding="utf-8") == source  # nothing inserted


def test_an_undefined_annotation_name_gets_its_typing_import_as_a_hint(tmp_path: Path) -> None:
    """§XXXVI (01, 2026-11-26): `experiment.py` used `Dict`, `List` and `Any` undefined in three repairs and none
    of them carried an import hint, because `typing` is not among the canonical packages."""
    from types import SimpleNamespace

    from adk.orchestration.findings import repair_findings
    from adk.orchestration.import_hints import importable_names

    h = SimpleNamespace(edges={})
    source = "def run():\n    cfg: Dict[str, Any] = {}\n    rows: List[int] = []\n"
    (tmp_path / "experiment.py").write_text(source, encoding="utf-8")
    issue = (
        "Ruff lint failure: experiment.py:2:10: F821 Undefined name `Dict`\n"
        "experiment.py:2:20: F821 Undefined name `Any`\nexperiment.py:3:11: F821 Undefined name `List`"
    )
    texts = [f.text for f in repair_findings([issue], tmp_path, lambda rel: importable_names(h, rel, {}))]
    assert "`from typing import Dict`" in texts[0] and "`from typing import Any`" in texts[1] and "`from typing import List`" in texts[2]
    assert (tmp_path / "experiment.py").read_text(encoding="utf-8") == source  # nothing inserted


def test_an_undefined_constant_of_the_file_itself_is_hinted_from_its_own_interface(tmp_path: Path):
    from types import SimpleNamespace

    from adk.orchestration.findings import repair_findings
    from adk.orchestration.import_hints import importable_names, own_declarations

    own = SimpleNamespace(type="I", id="I:experiment.py", spec={"import": "experiment", "uses": {"subspace.py": ["Detector", "N"]}, "symbols": {
        "N_ESTIMATORS": {"kind": "const", "type": "int"}, "run": {"kind": "func"}}})
    producer = SimpleNamespace(type="I", id="I:subspace.py", spec={"import": "subspace", "symbols": {"N": {"kind": "const"}, "Detector": {"kind": "class"}}})
    other = SimpleNamespace(type="I", id="I:other.py", spec={"import": "other", "symbols": {"N": {"kind": "const"}}})  # makes `N` ambiguous
    h = SimpleNamespace(edges={e.id: e for e in (own, producer, other)})
    (tmp_path / "experiment.py").write_text("def run():\n    return N_ESTIMATORS + N\n", encoding="utf-8")
    issue = "Ruff lint failure: experiment.py:2:12: F821 Undefined name `N_ESTIMATORS`\nexperiment.py:2:29: F821 Undefined name `N`"
    texts = [f.text for f in repair_findings([issue], tmp_path, lambda rel: importable_names(h, rel, {}), lambda rel: own_declarations(h, rel))]
    assert "`N_ESTIMATORS: int` is declared by the planned interface of this file" in texts[0]
    assert "`from subspace import N`" in texts[1]  # the file's own `uses` settles the ambiguous name


def test_a_pytest_finding_shows_the_call_that_passed_the_argument(tmp_path: Path):
    from adk.orchestration.findings import repair_findings

    (tmp_path / "tests").mkdir()
    (tmp_path / "trainer.py").write_text("def train(agent):\n    state = [1, 2]\n    agent.update(state)\n", encoding="utf-8")
    (tmp_path / "agent.py").write_text("class A:\n    def update(self, s):\n        return s in {}\n", encoding="utf-8")
    (tmp_path / "tests/test_trainer.py").write_text("def test_t():\n    pass\n", encoding="utf-8")
    issue = (
        "Pytest failure:\n_____ test_t _____\ntests/test_trainer.py:2: in test_t\n    train(A())\n"
        "trainer.py:3: in train\n    agent.update(state)\nagent.py:3: in update\n    return s in {}\nE TypeError: unhashable type: 'list'\n"
    )
    [finding] = repair_findings([issue], tmp_path)
    assert finding.file == "agent.py" and "called from trainer.py:3 (`agent.update(state)`)" in finding.text
    direct = issue.replace("trainer.py:3: in train\n    agent.update(state)\n", "")
    assert "called from" not in repair_findings([direct], tmp_path)[0].text  # the test itself called the code


def test_the_used_part_of_an_interface_is_the_named_definitions_with_their_docstrings():
    from adk.orchestration.interface_view import used_part

    src = (
        'import numpy as np\n\nN: int = 3\n\nclass A:\n    """A."""\n    def f(self) -> tuple[int, int]:\n        """Pair."""\n        ...\n\n'
        'def g(x: int) -> int:\n    """G."""\n    ...\n\ndef h() -> None:\n    ...\n'
    )
    part = used_part(src, ["A", "g"])
    assert "def f(self) -> tuple[int, int]" in part and '"""Pair."""' in part and "def g(x: int) -> int" in part
    assert "def h" not in part and "N: int" not in part
    assert "def h" in used_part(src, [])  # no names: the whole interface


def test_the_tester_reads_the_full_interface_of_the_module_under_test(tmp_path: Path):
    orch, _h = _planned(tmp_path)
    blueprint = {"interfaces": {"core.py": "def f() -> tuple[int, int]:\n    \"\"\"Pair.\"\"\"\n    ...\n"}}
    orch.blueprint_path.write_text(__import__("json").dumps(blueprint), encoding="utf-8")
    context = orch._context_for("tests/test_core.py", "tests/test_core.py")
    assert "def f() -> tuple[int, int]" in context["specification"]["core.py"]["interface"]
    assert "symbols" in context["specification"]["core.py"]  # σ stays


def test_the_coder_reads_only_what_it_uses_of_its_dependencies(tmp_path: Path):
    orch, h = _planned(tmp_path)
    uses = h.edges["I:core.py"].spec.get("uses", {})
    assert "config.py" in uses  # the fixture's core.py uses config.py
    blueprint = {"interfaces": {
        "config.py": "".join(f"{n}: int = 1\n" for n in uses["config.py"]) + "OTHER: int = 2\n",
        "core.py": "def own() -> None:\n    ...\n",
    }}
    orch.blueprint_path.write_text(__import__("json").dumps(blueprint), encoding="utf-8")
    spec = orch._context_for("core.py", "core.py")["specification"]
    assert "OTHER" not in spec["config.py"]["interface"] and uses["config.py"][0] in spec["config.py"]["interface"]
    assert "interface" not in spec["core.py"]  # its own stub is in `existing_content`


def test_a_new_test_file_sees_the_signatures_of_every_code_module(tmp_path: Path) -> None:
    """U3: exports came from import edges, so a new test saw only plot_results.py (T7, T10)."""
    from tests.support.planned_projects import with_plan

    orch = _orch(tmp_path)
    (orch.workspace_dir / "src").mkdir()
    (orch.workspace_dir / "src" / "env.py").write_text(ENV_INTERFACE, encoding="utf-8")
    tasks = [{"task_id": "T7", "target_node": "tests/test_env.py", "description": "tests", "assigned_agent": "seed_tester"}]
    with_plan(orch, {"src/env.py": ENV_INTERFACE}, None, tasks)
    seen: dict[str, Any] = {}

    def _capture(_md: Any, payload: dict[str, Any], **_kwargs: Any) -> dict[str, Any]:
        seen.update(payload)
        return {"status": "ok", "output": {"test_file": "tests/test_env.py", "test_code": "def test_x() -> None:\n    assert True\n"}}

    orch._call_agent = _capture
    orch._execute_builder_step({"task_id": "T7", "target_node": "tests/test_env.py", "assigned_agent": "seed_tester"}, "SML")
    # The test of src/env.py sees that module's σ from H (its I bag), nothing of the rest of the project.
    assert "TicTacToeEnv.step" in seen["specification"]["src/env.py"]["symbols"]
    assert "exports" not in seen and "grounded_hypergraph_state" not in seen
    assert any("tests/" in item for item in seen["done_when"])


def test_writer_sees_the_whole_target_chapter_or_the_chapters_with_the_named_pointers() -> None:
    """A chapter was cut to 1500 characters before "replace the section"; CRITIC tasks saw only the last 600."""
    from adk.orchestration.building import _document_context

    ch1 = "## Rozdział 1: Wstęp\n" + "a" * 3000 + " KONIEC1"
    ch4 = "## Rozdział 4: Wyniki\nWynik \\ref_csv{results.csv} jest dobry. " + "b" * 2000
    doc = f"# Praca\n\n{ch1}\n\n{ch4}\n\n## Rozdział 6: Wnioski\nKoniec pracy.\n"
    whole = _document_context(doc, "Chapter 1: introduction in thesis.md")
    assert "KONIEC1" in whole and "CHAPTER 1" in whole
    critic = _document_context(doc, "Fix thesis.md: [K1] Unresolved pointer: \\ref_csv{results.csv}")
    assert "\\ref_csv{results.csv} jest dobry" in critic and "KONIEC1" not in critic
    assert "LAST 600" in _document_context(doc, "Fix the style of thesis.md")


def test_repair_payload_carries_the_source_of_the_failing_tests(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    (orch.workspace_dir / "test_agent.py").write_text(
        "class TestAgent:\n    def test_act(self) -> None:\n        assert 1 == 2\n\n\ndef test_other() -> None:\n    pass\n",
        encoding="utf-8",
    )
    report = {
        "status": "FAIL",
        "supervisors": {
            "code_auditor": {
                "issues": ["Pytest failure: F.\nFAILED test_agent.py::TestAgent::test_act - assert 1 == 2\n1 failed, 1 passed"]
            }
        },
    }
    orch.validation_report_path.write_text(json.dumps(report), encoding="utf-8")

    failing = orch._failing_test_sources()

    assert list(failing) == ["test_agent.py::TestAgent::test_act"]
    assert failing["test_agent.py::TestAgent::test_act"]["error"] == "assert 1 == 2"
    assert "def test_act" in failing["test_agent.py::TestAgent::test_act"]["source"]


def test_a_repair_of_one_chapter_also_shows_the_chapter_that_holds_the_pointer_it_names() -> None:
    """§XXXVII.5: the full repair of chapter 4 had a target and the `elif` never showed chapter 3, where the pointer was broken."""
    from adk.orchestration.building import _document_context

    ch3 = "## Rozdział 3: Metoda\nZob. \\ref_ast{evaluator.py:evaluate_games} tu. KONIEC3"
    ch4 = "## Rozdział 4: Wyniki\nWynik. KONIEC4"
    doc = f"# Praca\n\n{ch3}\n\n{ch4}\n"
    both = _document_context(doc, "Chapter 4: Wyniki. Fix \\ref_ast{evaluator.py:evaluate_games}")
    assert "KONIEC3" in both and "KONIEC4" in both
    only_target = _document_context(doc, "Chapter 4: Wyniki.")
    assert "KONIEC4" in only_target and "KONIEC3" not in only_target


def test_the_coder_reads_its_own_planned_interface_once_the_file_is_no_longer_a_stub(tmp_path: Path):
    """§XXXVIII.3: after the first write the docstring of the plan is gone from the file, and the tester judges against it."""
    orch, _h = _planned(tmp_path)
    own = 'def own() -> dict:\n    """Return the keys episode_rewards and wins."""\n    ...\n'
    orch.blueprint_path.write_text(__import__("json").dumps({"interfaces": {"core.py": own}}), encoding="utf-8")
    (orch.workspace_dir / "core.py").write_text('def own() -> dict:\n    """Run."""\n    return {"reward_history": []}\n', encoding="utf-8")
    assert "episode_rewards" in orch._context_for("core.py", "core.py")["specification"]["core.py"]["interface"]


def test_writers_get_what_the_keys_stand_for_and_what_the_plan_says_the_thesis_is(tmp_path: Path):
    """§XXXVIII.3 / P3: bare BibTeX keys made the authors guess at papers; `thesis_statement`, `baseline_comparison` and `metrics` never arrived."""
    orch, h = _planned(tmp_path)
    (orch.workspace_dir / "references.bib").write_text(
        "@article{deka2022arc,\n  title = {Adaptive Q-learning},\n  author = {Deka, A. and Roy, B.},\n  year = {2022}\n}\n", encoding="utf-8"
    )
    blueprint = {
        "literature_recon": {"available_citation_keys": ["deka2022arc"]}, "thesis_statement": "Q beats random.",
        "baseline_comparison": "vs random", "metrics": ["win_rate"],
    }
    orch.blueprint_path.write_text(__import__("json").dumps(blueprint), encoding="utf-8")
    context = orch._document_context_slice(h)
    assert context["references"] == [{"key": "deka2022arc", "title": "Adaptive Q-learning", "authors": "Deka, A. and Roy, B.", "year": "2022"}]
    assert context["thesis_statement"] == "Q beats random." and context["metrics"] == ["win_rate"] and context["baseline_comparison"] == "vs random"
    assert context["available_citation_keys"] == ["deka2022arc"]


def test_a_repair_does_not_get_the_code_of_its_focus_symbols_twice(tmp_path: Path):
    """§XXXVIII.2 / P2: `repair_focus` carries the code to fix and `existing_content` carried the whole file with it again."""
    orch = _orch(tmp_path)
    code = "import os\n\n\ndef keep() -> int:\n    return 1\n\n\ndef broken() -> int:\n    return undefined_name\n"
    (orch.workspace_dir / "core.py").write_text(code, encoding="utf-8")
    seen: dict[str, Any] = {}

    def capture(_md: Any, payload: dict[str, Any], **_kw: Any) -> dict[str, Any]:
        seen.update(payload)
        return {"status": "ok", "output": {"files": [{"filename": "core.py", "content": code}]}}

    orch._call_agent = capture
    focus = symbol_sources(orch.workspace_dir, "core.py", ["broken"])
    task = {"task_id": "T2_FIX1", "target_node": "core.py", "description": "fix", "assigned_agent": "seed_coder", "repair_focus": {"file": "core.py", "symbols": focus}}
    orch._execute_builder_step(task, "SML")
    assert "undefined_name" not in seen["existing_content"] and "def keep()" in seen["existing_content"] and "import os" in seen["existing_content"]
    assert "undefined_name" in seen["task"]["repair_focus"]["symbols"]["broken"]
