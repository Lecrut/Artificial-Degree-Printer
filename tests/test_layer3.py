from __future__ import annotations

import os
import time
from pathlib import Path

from adk.core.llm import call_agent
from adk.tools.verification import compile_symbolic_references, run_isolated_tests


def test_runner_sees_sources_when_workspace_lives_under_benchmarks(tmp_path: Path):
    ws = tmp_path / "adk" / "workspace" / "benchmarks" / "_evolved_adk_state" / "workspace"
    ws.mkdir(parents=True)
    (ws / "core.py").write_text("def value() -> int:\n    return 1\n", encoding="utf-8")
    (ws / "test_core.py").write_text("from core import value\ndef test_value():\n    assert value() == 1\n", encoding="utf-8")

    res = run_isolated_tests(ws, use_docker=False)
    assert res["pytest_passed"] is True
    assert "No Python files" not in res["stdout"]


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


def test_gate_3_does_not_send_a_missing_pdf_back_to_the_writer(tmp_path: Path):
    """A missing thesis.pdf is the publisher's job. Gate 3 must not fail the thesis over it."""
    import shutil
    from adk.orchestrator import NeuroSymbolicOrchestrator

    src_adk = Path(__file__).resolve().parent.parent / "adk"
    dst_adk = tmp_path / "adk"
    shutil.copytree(src_adk / "state", dst_adk / "state")
    shutil.copytree(src_adk / "agents", dst_adk / "agents")
    shutil.copytree(src_adk / "tools", dst_adk / "tools")
    ws = dst_adk / "workspace"
    ws.mkdir(parents=True, exist_ok=True)

    # Seed valid code and test
    (ws / "config.py").write_text("ALPHA = 0.1\n", encoding="utf-8")
    (ws / "core.py").write_text("def run(): pass\n", encoding="utf-8")
    (ws / "test_core.py").write_text("def test_ok(): assert True\n", encoding="utf-8")
    (ws / "results.csv").write_text("method,score\nbaseline,0.5\nproposed,0.9\n", encoding="utf-8")
    (ws / "references.bib").write_text("@article{key1, author={Author}, title={Title}, year={2024}}\n", encoding="utf-8")
    (ws / "thesis.md").write_text(
        "## Rozdział 1: Wstęp\nCel \\ref_ast{config.py:ALPHA}.\n"
        "## Rozdział 2: SOTA\nPrzegląd \\cite{key1}.\n"
        "## Rozdział 3: Architektura\nModel.\n"
        "## Rozdział 4: Implementacja\nKod.\n"
        "## Rozdział 5: Wyniki\nWyniki \\ref_csv{results.csv:score}.\n"
        "## Rozdział 6: Podsumowanie\nWnioski.\n",
        encoding="utf-8",
    )

    orch = NeuroSymbolicOrchestrator(adk_root=dst_adk, enable_layer4=False, include_docs=True, provider="mock")
    defense_task = {"task_id": "GATE_3_DEFENSE", "target_node": "v4", "assigned_agent": "seed_writer"}

    report = orch._run_verification_step(defense_task, include_docs=True, is_final_gate=True)
    assert report["status"] == "PASS"
    all_issues = " ".join(report.get("issues", []))
    assert "thesis.pdf" not in all_issues.lower()


def test_experiment_overwrites_pasted_results_csv(tmp_path: Path):
    from adk.tools.building.experiment_runner import execute_workspace_experiment

    (tmp_path / "core.py").write_text(
        "def train_and_evaluate(csv_out_path='results.csv'):\n"
        "    from pathlib import Path\n"
        "    Path(csv_out_path).write_text('method,win_rate\\nproposed,0.5\\n', encoding='utf-8')\n",
        encoding="utf-8",
    )
    (tmp_path / "results.csv").write_text("method,win_rate\nbaseline,0.1\n", encoding="utf-8")

    result = execute_workspace_experiment(tmp_path)
    written = (tmp_path / "results.csv").read_text(encoding="utf-8")
    assert result["ok"] is True
    assert "proposed,0.5" in written
    assert "baseline,0.1" not in written


def test_mock_queue_does_not_compile_pdf(tmp_path: Path):
    from adk.orchestrator import NeuroSymbolicOrchestrator

    orch = NeuroSymbolicOrchestrator(adk_root=tmp_path, enable_layer4=False, provider="mock")
    assert orch._pdf_failure_report() is None




def test_declared_entrypoint_in_subpackage_runs_without_arguments(tmp_path: Path):
    from adk.tools.building.experiment_runner import execute_workspace_experiment

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "settings.py").write_text('OUT = "metrics.csv"\n', encoding="utf-8")
    (tmp_path / "src" / "train.py").write_text(
        "from pathlib import Path\nimport settings\n\ndef main():\n"
        "    Path(settings.OUT).write_text('method,metric,value\\nproposed,acc,0.9\\n', encoding='utf-8')\n",
        encoding="utf-8",
    )
    result = execute_workspace_experiment(tmp_path, entrypoint="src/train.py:main")
    assert result["ok"] is True, result["error"]
    assert (tmp_path / "metrics.csv").exists()


def test_entrypoint_with_required_arguments_is_reported_not_fed(tmp_path: Path):
    from adk.tools.building.experiment_runner import execute_workspace_experiment

    (tmp_path / "core.py").write_text("def train_and_evaluate(csv_out_path, seed):\n    return 1\n", encoding="utf-8")
    result = execute_workspace_experiment(tmp_path)
    assert result["ok"] is False
    assert "csv_out_path" in result["error"]


def test_missing_declared_entrypoint_is_an_error(tmp_path: Path):
    from adk.tools.building.experiment_runner import execute_workspace_experiment

    result = execute_workspace_experiment(tmp_path, entrypoint="src/nope.py:main")
    assert result["ok"] is False


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
