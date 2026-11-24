r"""§XXIV (2026-11-24, 01): a prose error must not destroy the data; pointer targets are complete; `\\pi` compiles."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from adk.orchestration.context import _results_targets
from adk.orchestration.factual_audit import thesis_missing_chapters
from adk.orchestration.recovery import RecoveryMixin
from adk.tools.building.doc_editor import edit_document_section
from adk.tools.verification.ref_compiler import compile_symbolic_references

_CSV = "method,metric,value\nq_learning,win_rate,0.9\nbaseline,win_rate,0.4\n"


def _workspace(tmp_path: Path) -> Path:
    (tmp_path / "results.csv").write_text(_CSV, encoding="utf-8")
    return tmp_path


def test_available_rows_are_complete_pointers(tmp_path: Path):
    columns, rows = _results_targets(_workspace(tmp_path), ["results.csv"])
    assert "results.csv:q_learning+win_rate:value" in rows
    assert "results.csv:value" in columns


def test_row_pointer_without_column_says_what_to_append(tmp_path: Path):
    ws = _workspace(tmp_path)
    thesis = ws / "thesis.md"
    thesis.write_text("## Rozdział 1\nWynik \\ref_csv{results.csv:q_learning+win_rate}.\n", encoding="utf-8")
    errors = compile_symbolic_references(thesis, ws)["errors"]
    assert any("names no column" in e and "q_learning+win_rate:value" in e for e in errors)
    assert not any("not found" in e for e in errors)


def test_complete_row_pointer_resolves(tmp_path: Path):
    ws = _workspace(tmp_path)
    thesis = ws / "thesis.md"
    thesis.write_text("## Rozdział 1\nWynik \\ref_csv{results.csv:q_learning+win_rate:value}.\n", encoding="utf-8")
    assert not compile_symbolic_references(thesis, ws)["errors"]


def test_json_escaped_backslashes_are_single_in_a_saved_section(tmp_path: Path):
    thesis = tmp_path / "thesis.md"
    edit_document_section(thesis, "Rozdział 2", r"Wzór $$ V_\\pi(s) = \\mathbb{E} $$ i łamanie \\ dalej.")
    text = thesis.read_text(encoding="utf-8")
    assert r"V_\pi(s)" in text and r"\mathbb{E}" in text and r"\\pi" not in text
    assert r"łamanie \\ dalej" in text  # a line break stays


def test_a_doubled_backslash_that_survived_is_reported(tmp_path: Path):
    ws = _workspace(tmp_path)
    thesis = ws / "thesis.md"
    thesis.write_text("## Rozdział 1\n" + r"$$ V_\\pi(s) $$" + "\n", encoding="utf-8")
    assert any("Doubled backslash" in e for e in compile_symbolic_references(thesis, ws)["errors"])


def test_roman_chapter_numbers_count():
    thesis = "## Rozdział I: A\n\n## Rozdział 2: B\n\n## Rozdział VI: C\n"
    assert thesis_missing_chapters(thesis, {n: "" for n in range(1, 7)}) == [3, 4, 5]


def _report(issues: list[str]) -> dict:
    return {"failed_file": "thesis.md", "issues": issues}


def test_pointer_findings_stay_with_the_writer_while_results_exist(tmp_path: Path):
    fixed = RecoveryMixin._pointer_fix_is_writers
    me = SimpleNamespace(workspace_dir=tmp_path)
    issues = ["Column 'q_learning+win_rate' not found in 'results.csv'"]
    assert not fixed(me, _report(issues), "experiment.py")  # no results yet: the producer may be at fault
    _workspace(tmp_path)
    assert fixed(me, _report(issues), "experiment.py")
    assert not fixed(me, _report(issues), "thesis.md")  # already the writer's
    assert not fixed(me, _report(issues + ["Unbalanced TikZ environment: 1 begin vs 0 end."]), "experiment.py")


def test_a_prose_repair_that_breaks_the_experiment_is_restorable(tmp_path: Path):
    from adk.orchestration.building import BuildingMixin

    ws = _workspace(tmp_path)
    (ws / "experiment.py").write_text("OLD = 1\n", encoding="utf-8")
    me = SimpleNamespace(workspace_dir=ws, _last_experiment_error="")
    guard = BuildingMixin._guard_results_from_prose_fix(me, _report([]), "experiment.py")
    assert guard is not None
    (ws / "experiment.py").write_text("BROKEN = 2\n", encoding="utf-8")
    (ws / "results.csv").unlink()
    BuildingMixin._restore_files(me, guard)
    assert (ws / "experiment.py").read_text(encoding="utf-8") == "OLD = 1\n"
    assert (ws / "results.csv").read_text(encoding="utf-8") == _CSV
    # Not a document failure, no results, or the experiment already failing: nothing to guard.
    assert BuildingMixin._guard_results_from_prose_fix(me, {"failed_file": "agent.py"}, "experiment.py") is None
    me._last_experiment_error = "KeyError"
    assert BuildingMixin._guard_results_from_prose_fix(me, _report([]), "experiment.py") is None
