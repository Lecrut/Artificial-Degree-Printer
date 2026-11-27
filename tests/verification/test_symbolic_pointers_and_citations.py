"""Symbolic pointers (ref_ast, ref_csv, ref_fig) and citations in the thesis: how they resolve, what an unresolved one tells the writer, which findings stay with the writer, bare math and doubled backslashes."""

from __future__ import annotations

import os
import time
from pathlib import Path

from adk.core.llm import call_agent
from adk.orchestration.context import _results_targets
from adk.orchestration.write_gate import _plain_symbol
from adk.orchestrator import NeuroSymbolicOrchestrator
from adk.tools.building.doc_editor import edit_document_section
from adk.tools.verification import compile_symbolic_references
from tests.support.adk_sandbox import _clone_adk_env
from tests.support.failed_vertex_project import _planned
from tests.support.orchestrator_sandbox import _orch
from tests.support.results_pointer_workspace import _workspace
from tests.support.staged_planning import _make_orch


def _errors(ws: Path, thesis: str) -> list[str]:
    (ws / "thesis.md").write_text(thesis, encoding="utf-8")
    return compile_symbolic_references(ws / "thesis.md", ws, write_compiled=False)["errors"]


def test_symbols_with_py_inside_and_class_prefix_are_normalized() -> None:
    """2026-11-14: `src/experiment/experiment_runner.py.run_all` and `class Player` were rejected."""
    assert _plain_symbol("src/experiment/experiment_runner.py.run_all") == ("run_all", "src/experiment/experiment_runner.py")
    assert _plain_symbol("class Player") == ("Player", None)
    assert _plain_symbol("def main") == ("main", None)


def test_unresolved_pointer_hint_names_the_closest_real_target(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "config.py").write_text("class SignalConfig:\n    pass\n", encoding="utf-8")
    (ws / "thesis.md").write_text(
        "# Praca\nZob. \\ref_ast{generator.py:SignalConfig} i \\ref_ast{file:symbol}.\n", encoding="utf-8"
    )

    res = compile_symbolic_references(ws / "thesis.md", ws, write_compiled=False)

    assert any("config.py:SignalConfig" in e for e in res["errors"])
    assert any("placeholder" in e for e in res["errors"])


def test_pointer_naming_a_directory_is_a_finding_not_a_crash(tmp_path: Path) -> None:
    r"""2026-11-15: `\ref_ast{src:evaluation.py:f}` named the directory `src`; reading it raised PermissionError
    and crashed the run. A wrong pointer is a finding with the corrected form."""
    ws = tmp_path / "ws"
    (ws / "src").mkdir(parents=True)
    (ws / "src" / "evaluation.py").write_text("def evaluate_agent() -> None:\n    pass\n", encoding="utf-8")
    (ws / "thesis.md").write_text(r"Zob. \ref_ast{src:evaluation.py:evaluate_agent}." + "\n", encoding="utf-8")

    res = compile_symbolic_references(ws / "thesis.md", ws, write_compiled=False)

    assert res["status"] == "FAIL"
    assert any("src/evaluation.py:evaluate_agent" in e for e in res["errors"])


def test_pointer_findings_are_the_writers_whatever_file_they_name():
    """X6, 02: "Symbol 'CONFIG' not found in 'config.py'" became a coder task on src/config.py."""
    from adk.orchestration.recovery import _is_pointer_finding

    assert _is_pointer_finding("Symbol 'CONFIG' not found in 'config.py' Closest existing targets: src/config.py:CHANNELS.")
    assert _is_pointer_finding("File 'src' does not exist (it is a directory, not a file) A path inside a pointer is separated by a slash")
    assert not _is_pointer_finding("Import error in experiment.py: ImportError: cannot import name 'N_REPETITIONS'")


def test_writer_is_told_there_are_no_results_yet_instead_of_choosing_from_an_empty_list(tmp_path: Path) -> None:
    """R2: 01 wrote chapters 1–3 before the experiment; 12x "CSV file 'ttt_results' does not exist" after a hint to
    pick a target from `available_csv_columns`, which was empty."""
    errors = _errors(tmp_path, "Wyniki \\ref_csv{ttt_results:mean_reward} i \\ref_csv{ttt_results:n_runs}, \\ref_csv{x}.\n")
    assert len(errors) == 1
    assert "No results exist yet" in errors[0] and "Remove every \\ref_csv" in errors[0]
    assert "available_csv_columns" not in errors[0]


def test_writer_is_pointed_at_results_csv_when_results_exist(tmp_path: Path) -> None:
    (tmp_path / "results.csv").write_text("method,metric,value\nq,win_rate,0.9\n", encoding="utf-8")
    errors = _errors(tmp_path, "Wynik \\ref_csv{ttt_results:win_rate}.\n")
    assert errors == [
        "\\ref_csv{ttt_results:win_rate}: no such file. The results are in results.csv: write "
        "\\ref_csv{results.csv:win_rate} with a column from 'available_csv_columns'."
    ]


def test_a_citation_the_bibliography_lacks_never_enters_the_thesis(tmp_path: Path) -> None:
    """03: `dijkstra1959` stayed in the document after its task failed and failed every later section (2 -> 21 errors)."""
    orch = _make_orch(tmp_path)
    (orch.workspace_dir / "references.bib").write_text("@article{tang2026scaling,\n title={X}\n}\n", encoding="utf-8")
    text = orch._known_citations_only(r"Dijkstra~\cite{dijkstra1959}. Scaling \cite{tang2026scaling, wah2016}.")
    assert text == r"Dijkstra. Scaling \cite{tang2026scaling}."


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


def test_pending_results_do_not_excuse_ref_csv_or_placeholder_in_early_chapter(tmp_path: Path):
    """02 T1: `#ch1` wrote `\\ref_csv{<file>:<method>+F1:value}` before `results.csv` existed; `pending_files` hid it."""
    orch, _h = _planned(tmp_path)
    (orch.workspace_dir / "thesis.md").write_text(
        "## Rozdział 1: Wstęp\nMetryka \\ref_csv{<file>:<method>+F1:value} i wykres \\ref_fig{figures/f1.png}.\n",
        encoding="utf-8",
    )
    orch._get_pending_future_files = lambda _t: {"results.csv", "figures", "figures.py"}
    report = orch._run_verification_step(
        {"task_id": "T1", "target_node": "thesis.md#ch1", "assigned_agent": "seed_writer"},
        include_docs=True,
        is_final_gate=False,
    )
    issues = report["supervisors"]["symbolic_auditor"]["issues"]
    assert report["status"] == "FAIL"
    assert any("No results exist yet" in i or "<file>" in i for i in issues)
    assert not any("figures/f1.png" in i for i in issues)  # genuine pending figure still waits


def test_citations_without_bib_and_empty_cite_are_stripped(tmp_path: Path):
    """02: without `references.bib`, 5x `\\cite{available_ast_symbols}` and 8x `\\cite{}` entered `thesis.md`."""
    orch = _orch(tmp_path)
    cleaned = orch._known_citations_only(r"Tekst~\cite{available_ast_symbols} oraz szum \cite{} i \cite{ , }.")
    assert cleaned == "Tekst oraz szum i."


def test_bare_math_commands_outside_math_mode_are_reported_while_wrapped_math_passes(tmp_path: Path):
    """02: XeTeX crashed on `Dla każdego wektora \\mathbf{x} i subsetu \\mathcal{S}_m` outside `$...$`."""
    bad = tmp_path / "bad.md"
    bad.write_text("Dla wektora \\mathbf{x} i podprzestrzeni \\mathcal{S}_m liczymy \\sum_{m=1}^{M} s_m.\n", encoding="utf-8")
    res_bad = compile_symbolic_references(bad, tmp_path, write_compiled=False)
    assert res_bad["status"] == "FAIL"
    assert any("Math command outside math mode" in e and "\\mathbf" in e for e in res_bad["errors"])

    good = tmp_path / "good.md"
    good.write_text(
        "Dla wektora $\\mathbf{x}$ i $\\mathcal{S}_m$: $$ s(x) = \\frac{1}{M} \\sum_{m=1}^{M} s_m $$ oraz `\\mathbf{x}`.\n",
        encoding="utf-8",
    )
    res_good = compile_symbolic_references(good, tmp_path, write_compiled=False)
    assert res_good["status"] == "PASS" and not res_good["errors"]


def test_ref_compiler_resolves_and_checks_timestamps(tmp_path: Path):
    ws = tmp_path / "workspace"
    ws.mkdir()
    py_file = ws / "config.py"
    csv_file = ws / "results.csv"
    doc_file = ws / "thesis.md"

    py_file.write_text("THRESHOLD: float = 0.95\n", encoding="utf-8")
    csv_file.write_text("method,score\nbaseline,0.72\nproposed,0.98\n", encoding="utf-8")
    now = time.time()
    os.utime(py_file, (now - 10, now - 10))
    os.utime(csv_file, (now, now))

    doc_file.write_text(
        "Config threshold is \\ref_ast{config.py:THRESHOLD}, baseline is \\ref_csv{results.csv:baseline:score}, "
        "proposed is \\ref_csv{results.csv:proposed:score} (latest: \\ref_csv{results.csv:score}).\n",
        encoding="utf-8",
    )

    comp = compile_symbolic_references(doc_file, ws)
    assert comp["status"] == "PASS"
    assert "0.95" in comp["compiled_text"]
    assert "0.72" in comp["compiled_text"]
    assert "0.98" in comp["compiled_text"]

    os.utime(csv_file, (now - 100, now - 100))
    comp_stale = compile_symbolic_references(doc_file, ws)
    assert comp_stale["status"] == "FAIL"
    assert "results.csv" in comp_stale["stale_csv_files"]

    auditor_res = call_agent(
        "agents/verification/symbolic_auditor.md",
        {"issues": comp_stale["errors"]},
        model_tier="SML",
        provider="mock",
    )
    assert auditor_res["output"]["status"] == "FAIL"

    # Test BibTeX citation check, malformed tag detection, and AI fluff scanner
    os.utime(csv_file, (now + 10, now + 10))
    (ws / "references.bib").write_text("@article{vaswani2017attention, title={Attention}}\n", encoding="utf-8")
    doc_file.write_text(
        "To jest przełomowe podejście \\cite{vaswani2017attention,missing2026key} i \\ref_ast{config.py}.\n",
        encoding="utf-8",
    )
    comp_checks = compile_symbolic_references(doc_file, ws)
    assert comp_checks["status"] == "FAIL"
    assert "przełomowe podejście" in comp_checks["fluff_detected"]
    assert any("missing2026key" in err for err in comp_checks["errors"])
    assert any("Malformed symbolic tag" in err for err in comp_checks["errors"])


def test_ref_compiler_resolves_ref_fig_tags(tmp_path: Path):
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "convergence_plot.pdf").write_text("PDF_PLOT_CONTENT", encoding="utf-8")
    doc_file = ws / "thesis.md"

    doc_file.write_text(
        "Wykres zbieżności przedstawiono na \\ref_fig{convergence_plot.pdf} (oraz \\ref_fig{convergence_plot}).\n",
        encoding="utf-8",
    )
    comp_ok = compile_symbolic_references(doc_file, ws)
    assert comp_ok["status"] == "PASS"
    assert "[Ryc. convergence_plot.pdf]" in comp_ok["compiled_text"]
    assert "[Ryc. convergence_plot]" in comp_ok["compiled_text"]
    assert "\\ref_fig{convergence_plot.pdf}" in comp_ok["resolved_references"]

    doc_file.write_text("Brakujący wykres: \\ref_fig{nonexistent_chart.png}.\n", encoding="utf-8")
    comp_missing = compile_symbolic_references(doc_file, ws)
    assert comp_missing["status"] == "FAIL"
    assert any("nonexistent_chart.png" in err for err in comp_missing["errors"])


def test_tidy_csv_pointer_selects_row_by_method_and_metric(tmp_path: Path):
    from adk.tools.verification import compile_symbolic_references

    (tmp_path / "results.csv").write_text(
        "method,metric,value,std_dev\nproposed,win_rate,0.58,0.02\nbaseline,win_rate,0.33,0.01\nproposed,draw_rate,0.12,0.01\n",
        encoding="utf-8",
    )
    doc = tmp_path / "thesis.md"
    doc.write_text(
        "Agent: \\ref_csv{results.csv:proposed+win_rate:value}, baseline: \\ref_csv{results.csv:baseline+win_rate:value}.\n",
        encoding="utf-8",
    )
    res = compile_symbolic_references(doc, tmp_path, write_compiled=False)
    assert res["status"] == "PASS", res["errors"]
    assert "0.58" in res["compiled_text"] and "0.33" in res["compiled_text"]


def test_a_chapter_may_cite_what_h_holds(tmp_path: Path):
    """The writer's pointer targets come from H: the planned modules' symbols (σ) and the experiment's outputs.
    A CSV the plan does not produce is not offered (it used to be: every CSV on disk was "the graph")."""
    from tests.support.planned_projects import with_plan

    adk_dir = _clone_adk_env(tmp_path)
    orch = NeuroSymbolicOrchestrator(adk_root=adk_dir, provider="mock")
    ws = orch.workspace_dir
    (ws / "results.csv").write_text("method,metric,value\nproposed,win_rate,0.5\n", encoding="utf-8")
    (ws / "ablation.csv").write_text("method,metric,value\nbaseline,loss_rate,0.2\n", encoding="utf-8")
    config = '"""Config."""\nALPHA: float = 0.1\nEPISODES: int = 10\n'
    core = '"""Core."""\nimport config\n\n\ndef train_and_evaluate() -> float:\n    """Train."""\n'
    chapters = [{"index": 1, "title": "Wstęp", "focus": "cel"}]
    with_plan(orch, {"config.py": config, "core.py": core}, "core.py:train_and_evaluate", [], chapters)

    may_cite = orch._context_for("thesis.md#ch1", "thesis.md")["may_cite"]
    assert {"config.py:ALPHA", "config.py:EPISODES", "core.py:train_and_evaluate"} <= set(may_cite["available_ast_symbols"])
    assert "config.py" not in may_cite["available_ast_symbols"]
    assert "results.csv:value" in may_cite["available_csv_columns"]
    assert "results.csv:proposed+win_rate:value" in may_cite["available_csv_rows"]
    assert not any(c.startswith("ablation.csv") for c in may_cite["available_csv_columns"])


def test_results_pointer_findings_wait_for_green_code_and_refs_join_the_critic(tmp_path: Path) -> None:
    """U9: Q1-Q4 each gave the writer CRITIC + REFS on \\ref_csv while results.csv did not exist."""
    orch = _orch(tmp_path)
    red = orch._tasks_from_audit(
        {
            "pytest_status": "FAIL",
            "pytest_errors": ["pytest nie przechodzi"],
            "symbolic_errors": ["CSV file 'results.csv' does not exist", "Malformed tag \\ref_ast{Agent.move}"],
            "trigger_issues": ["Unresolved pointer: \\ref_csv{results.csv}"],
        },
        1,
    )
    ids = [t["task_id"] for t in red]
    assert not any(i.endswith("_REFS") for i in ids)
    critic = next(t for t in red if t["task_id"].endswith("_CRITIC"))
    assert "ref_ast{Agent.move}" in critic["description"] and "ref_csv" not in critic["description"]

    green = orch._tasks_from_audit(
        {"pytest_status": "PASS", "csv_columns": ["method"], "symbolic_errors": ["CSV row 'x' does not exist"], "trigger_issues": ["Teza bez liczby."]},
        2,
    )
    assert [t["task_id"] for t in green] == ["Q2_CRITIC"]
    assert "[K1]" in green[0]["description"] and "[K2]" in green[0]["description"]


def test_a_pointer_finding_names_the_pointer_so_the_repair_sees_the_chapter_that_holds_it(tmp_path: Path) -> None:
    """§XXXVI (01, 2026-11-26): chapter 3 cited `evaluate_games`, renamed by a redesign; the finding named only the
    symbol, so the repairs of chapters 4-6 saw the end of the document and failed nine times with the same error."""
    from adk.orchestration import agent_texts as texts
    from adk.orchestration.building import _document_context

    (tmp_path / "evaluator.py").write_text('def evaluate_symmetric() -> None:\n    """Evaluates."""\n', encoding="utf-8")
    chapter3 = "## Rozdział 3: Środowisko\nPorównanie liczy \\ref_ast{evaluator.py:evaluate_games}.\n"
    thesis = "## Rozdział 1: Wstęp\nTekst.\n\n## Rozdział 2: Metoda\nTekst.\n\n" + chapter3 + "\n## Rozdział 4: Wyniki\n" + "Zakończenie. " * 80
    errors = _errors(tmp_path, thesis)

    assert errors and "\\ref_ast{evaluator.py:evaluate_games}" in errors[0] and "not found" in errors[0]
    description = texts.focused_repair_description("thesis.md", [], errors)
    assert "Porównanie liczy" in _document_context(thesis, description)  # chapter 3 is shown to the one who repairs


def test_an_unclosed_pointer_does_not_swallow_the_next_paragraphs(tmp_path: Path) -> None:
    r"""§XXXVII.5: `\ref_ast{random_agent.py:RandomAgent` without `}` matched up to the `}` of a pointer two paragraphs later."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "trainer.py").write_text("class Trainer:\n    pass\n", encoding="utf-8")
    errors = _errors(tmp_path, "Agent `\\ref_ast{random_agent.py:RandomAgent` gra.\n\nDrugi akapit.\n\nTrener \\ref_ast{src/trainer.py:Trainer}.\n")
    assert any("Unclosed symbolic tag" in e for e in errors)
    assert not any("Drugi akapit" in e for e in errors)  # the old message quoted the swallowed paragraphs
