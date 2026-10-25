from __future__ import annotations

import os
import time
from pathlib import Path

from adk.core.llm import call_agent
from adk.tools.verification import compile_symbolic_references, run_isolated_tests


def test_isolated_test_runner_pass_and_fail(tmp_path: Path):
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "math_mod.py").write_text("def add(a: int, b: int) -> int:\n    return a + b\n", encoding="utf-8")
    (ws / "test_math.py").write_text("from math_mod import add\ndef test_add():\n    assert add(2, 3) == 5\n", encoding="utf-8")

    res_pass = run_isolated_tests(ws, use_docker=False)
    assert res_pass["status"] == "PASS"
    assert res_pass["pytest_passed"] is True

    (ws / "test_math.py").write_text("from math_mod import add\ndef test_add():\n    assert add(2, 3) == 999\n", encoding="utf-8")
    res_fail = run_isolated_tests(ws, use_docker=False)
    assert res_fail["status"] == "FAIL"
    assert res_fail["pytest_passed"] is False


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

