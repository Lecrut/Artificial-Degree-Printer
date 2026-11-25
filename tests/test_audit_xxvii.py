"""§XXVII: repairs after the 24.11 v2 run (01, 02)."""

from __future__ import annotations

from pathlib import Path

from adk.tools.building.experiment_runner import execute_workspace_experiment
from adk.tools.verification.ref_compiler import compile_symbolic_references
from tests.test_audit_xi import _planned, _RunState, FAILED
from tests.test_write_gate import _orch


def test_a_timeout_tells_the_coder_where_the_run_was_not_the_harness_script(tmp_path: Path):
    (tmp_path / "slow.py").write_text("import time\n\ndef main():\n    while True:\n        time.sleep(0.2)\n", encoding="utf-8")
    result = execute_workspace_experiment(tmp_path, timeout=13, entrypoint="slow.py:main")
    assert not result["ok"] and "exceeded 13s" in result["error"]
    assert "slow.py" in result["error"] and "_SNIPPET" not in result["error"] and "importlib" not in result["error"]


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

