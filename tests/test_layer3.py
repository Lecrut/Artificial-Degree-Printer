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

    py_file.write_text("THRESHOLD = 0.95\n", encoding="utf-8")
    csv_file.write_text("metric,score\nf1,0.98\n", encoding="utf-8")
    now = time.time()
    os.utime(py_file, (now - 10, now - 10))
    os.utime(csv_file, (now, now))

    doc_file.write_text(
        "Config threshold is \\ref_ast{config.py:THRESHOLD} and score is \\ref_csv{results.csv:score}.\n",
        encoding="utf-8",
    )

    comp = compile_symbolic_references(doc_file, ws)
    assert comp["status"] == "PASS"
    assert "0.95" in comp["compiled_text"]
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
