from __future__ import annotations

import ast
import importlib
import importlib.metadata
import re
import subprocess
import sys
from pathlib import Path

from adk.benchmarks import BENCHMARK_TASKS, get_benchmark_task, run_benchmark_suite
from adk.core.connection import LLMConnectionManager
from adk.tools.building.thesis_publisher import publish_workspace_thesis_bundle

REPO_ROOT = Path(__file__).resolve().parent.parent

PACKAGE_IMPORT_MAP = {
    "matplotlib": ["matplotlib", "matplotlib.pyplot", "matplotlib.backends.backend_pdf", "matplotlib.image"],
    "numpy": ["numpy"],
    "pillow": ["PIL", "PIL.Image"],
    "pytest": ["pytest"],
    "ruff": [],
}


def _parse_requirements_txt(req_path: Path) -> list[tuple[str, str | None]]:
    """Return list of (package_name, min_version) from requirements.txt."""
    specs: list[tuple[str, str | None]] = []
    for raw_line in req_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^([A-Za-z0-9_.-]+)(?:>=([0-9.]+))?", line)
        if match:
            specs.append((match.group(1).lower(), match.group(2)))
    return specs


def test_requirements_txt_exists_and_all_extensions_importable():
    """Verify requirements.txt exists and every listed package & submodule is installed and importable."""
    req_path = REPO_ROOT / "requirements.txt"
    assert req_path.exists(), "Brak pliku requirements.txt w katalogu głównym repozytorium!"

    parsed = _parse_requirements_txt(req_path)
    assert len(parsed) >= 5, f"Zbyt mało zależności w requirements.txt: {parsed}"

    required_names = {pkg for pkg, _ in parsed}
    for expected in ("matplotlib", "numpy", "pillow", "pytest", "ruff"):
        assert expected in required_names, f"Brak wymaganej paczki '{expected}' w requirements.txt"

    for pkg_name, _ in parsed:
        dist_version = importlib.metadata.version(pkg_name)
        assert dist_version, f"Paczka '{pkg_name}' nie ma zainstalowanych metadanych wersji"
        for mod_name in PACKAGE_IMPORT_MAP.get(pkg_name, [pkg_name]):
            mod = importlib.import_module(mod_name)
            assert mod is not None, f"Nie udało się zaimportować modułu '{mod_name}' z paczki '{pkg_name}'"


def test_local_venv_has_all_required_packages_and_cli_works():
    """Verify that .venv/Scripts/python.exe (if present) has matplotlib, pillow, numpy, pytest, ruff and runs main.py --check-llm."""
    venv_py = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
    target_py = str(venv_py) if venv_py.exists() else sys.executable

    check_code = (
        "import matplotlib, matplotlib.pyplot, matplotlib.backends.backend_pdf, PIL, numpy, pytest; "
        "print('ALL_EXTENSIONS_OK:', matplotlib.__version__, numpy.__version__, PIL.__version__)"
    )
    proc = subprocess.run(
        [target_py, "-c", check_code],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=25,
    )
    assert proc.returncode == 0, (
        f"Środowisko {target_py} nie posiada wszystkich rozszerzeń!\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}"
    )
    assert "ALL_EXTENSIONS_OK:" in proc.stdout

    # Also verify `python main.py --check-llm` runs cleanly via .venv python
    cli_proc = subprocess.run(
        [target_py, str(REPO_ROOT / "main.py"), "--check-llm"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=25,
    )
    assert cli_proc.returncode == 0, f"Błąd uruchomienia main.py --check-llm: {cli_proc.stderr}"
    assert "ADK Connection Manager" in cli_proc.stdout


def test_llm_connection_manager_diagnostics():
    """Verify LLMConnectionManager.check_llm_access returns complete diagnostic dictionary."""
    conn = LLMConnectionManager(provider="mock")
    diag = conn.check_llm_access()
    assert diag["configured_provider"] == "mock"
    assert diag["resolved_provider"] == "mock"
    assert "sml_model" in diag
    assert "lrm_model" in diag
    assert isinstance(diag["ollama"], dict)
    assert "reachable" in diag["ollama"]


def test_benchmark_tasks_specifications_and_syntax():
    """Verify all 4 benchmark tasks have valid AST in core_code, test_code, and plot_script."""
    assert set(BENCHMARK_TASKS.keys()) == {
        "01_rl_tictactoe",
        "02_ml_anomaly_detection",
        "03_graph_pathfinding",
        "04_federated_learning",
    }
    assert get_benchmark_task("1").task_id == "01_rl_tictactoe"
    assert get_benchmark_task("2").task_id == "02_ml_anomaly_detection"
    assert get_benchmark_task("3").task_id == "03_graph_pathfinding"
    assert get_benchmark_task("evolution").task_id == "03_graph_pathfinding"
    assert get_benchmark_task("4").task_id == "04_federated_learning"
    assert len(get_benchmark_task("4").custom_tasks) == 10

    # Greenfield vs Evolution verification
    assert get_benchmark_task("1").task_type == "greenfield"
    assert get_benchmark_task("2").task_type == "greenfield"
    assert get_benchmark_task("4").task_type == "greenfield"
    t3 = get_benchmark_task("3")
    assert t3.task_type == "evolution"
    assert "core.py" in t3.initial_workspace_files
    assert "config.py" in t3.initial_workspace_files
    assert "Dijkstra" in t3.initial_workspace_files["core.py"]

    for task_id, spec in BENCHMARK_TASKS.items():
        ast.parse(spec.core_code, filename=f"{task_id}_core.py")
        ast.parse(spec.test_code, filename=f"{task_id}_test.py")
        ast.parse(spec.plot_script, filename=f"{task_id}_plot.py")
        for sym_name, sym_code in spec.config_ast_nodes:
            assert sym_name in sym_code
            ast.parse(sym_code, filename=f"{task_id}_config.py")
        assert "\\ref_ast{" in spec.doc_section_content
        assert "\\ref_csv{" in spec.doc_section_content
        assert "\\ref_fig{" in spec.doc_section_content


def test_thesis_publisher_generates_pdf_tex_html_and_runner(tmp_path: Path):
    """Verify that publish_workspace_thesis_bundle executes code, generates plots, compiles refs, and writes valid PDF/LaTeX/HTML."""
    spec = get_benchmark_task("02_ml_anomaly_detection")
    ws = tmp_path / "anomaly_ws"
    ws.mkdir(parents=True, exist_ok=True)

    # Seed workspace files for task 2
    config_src = "".join(code for _, code in spec.config_ast_nodes)
    (ws / "config.py").write_text(config_src, encoding="utf-8")
    (ws / "core.py").write_text(spec.core_code, encoding="utf-8")
    (ws / "test_core.py").write_text(spec.test_code, encoding="utf-8")
    (ws / "plot_results.py").write_text(spec.plot_script, encoding="utf-8")
    (ws / "references.bib").write_text(spec.bibtex_entries, encoding="utf-8")
    (ws / "thesis.md").write_text(
        f"## {spec.sota_section_title}\n{spec.sota_section_content}\n\n"
        f"## {spec.doc_section_title}\n{spec.doc_section_content}\n",
        encoding="utf-8",
    )

    pub = publish_workspace_thesis_bundle(
        spec=spec,
        workspace_dir=ws,
        evolution_summary={"events_triggered": ["CREATE_AGENT", "SPLIT_AGENT"], "active_agents_count": 6, "elapsed_seconds": 0.42},
    )
    assert pub["symbolic_status"] == "PASS"
    assert pub["tex_symbolic_status"] == "PASS"
    assert pub["resolved_references_count"] >= 6

    pdf_file = Path(pub["pdf_path"])
    assert pdf_file.exists() and pdf_file.stat().st_size > 2000
    assert pdf_file.read_bytes().startswith(b"%PDF-")

    tex_file = Path(pub["tex_path"])
    compiled_tex = Path(pub["compiled_tex_path"])
    html_file = Path(pub["html_path"])
    runner_file = Path(pub["runner_script"])

    assert tex_file.exists() and "\\documentclass" in tex_file.read_text(encoding="utf-8")
    assert compiled_tex.exists() and "\\ref_ast{" not in compiled_tex.read_text(encoding="utf-8")
    assert html_file.exists() and "data:image/png;base64," in html_file.read_text(encoding="utf-8")
    assert runner_file.exists()


def test_benchmark_runner_single_task_in_isolated_tmp(tmp_path: Path):
    """Verify run_benchmark_suite executes multiple W1->W2->W3->W4->W1 cycles and generates full 6-chapter thesis PDF & JSON."""
    out_dir = tmp_path / "bench_out"
    res = run_benchmark_suite(task_keys=["2"], provider="mock", output_root=out_dir)
    assert res["status"] == "COMPLETED"
    assert len(res["tasks"]) == 1

    t_res = res["tasks"][0]
    assert t_res["orchestrator_status"] == "COMPLETED"
    # Verify multi-cycle architectural traversal (3 full W2->W3->W4->W1->W2->W3 loops across Code, Tests/CSV, and Thesis)
    assert t_res["replan_count"] == 3
    assert len(t_res["architecture_cycles"]) == 3
    assert [c["node_id"] for c in t_res["architecture_cycles"]] == ["v1", "v3", "v4"]
    assert all(c["w3_post_remediation_status"] == "PASS" for c in t_res["architecture_cycles"])

    # Verify Layer 4 self-evolution events (CREATE_AGENT + SPLIT_AGENT + MUTATE_AGENT + WEIGHT_ESCALATED)
    evo_events = t_res["evolution"]["new_events_in_task"]
    assert "AGENT_CREATED" in evo_events
    assert "AGENT_SPLIT" in evo_events
    assert "WEIGHT_ESCALATED" in evo_events

    # Verify all 6 chapters exist in compiled thesis.compiled.md and thesis.compiled.tex
    compiled_md = Path(t_res["artifacts"]["compiled_md_path"]).read_text(encoding="utf-8")
    compiled_tex = Path(t_res["artifacts"]["compiled_tex_path"]).read_text(encoding="utf-8")
    assert "Rozdział 1: Wstęp, Cel i Teza Pracy" in compiled_md
    assert "Rozdział 6: Podsumowanie, Wnioski i Kierunki Rozwoju" in compiled_md
    assert "\\ref_ast{" not in compiled_md
    assert "\\ref_csv{" not in compiled_md
    assert "\\ref_ast{" not in compiled_tex

    assert Path(res["master_summary_pdf"]).exists()
    assert Path(t_res["artifacts"]["pdf_path"]).exists()


def test_benchmark_task_4_federated_runs_10_tasks(tmp_path: Path):
    """Verify task 4 (04_federated_learning) runs all 10 custom tasks in isolated tmp and generates valid thesis bundle."""
    out_dir = tmp_path / "bench_out4"
    res = run_benchmark_suite(task_keys=["4"], provider="mock", output_root=out_dir)
    assert res["status"] == "COMPLETED"
    assert len(res["tasks"]) == 1
    t_res = res["tasks"][0]
    assert t_res["task_id"] == "04_federated_learning"
    assert t_res["orchestrator_status"] == "COMPLETED"
    assert Path(t_res["artifacts"]["pdf_path"]).exists()
    assert Path(t_res["artifacts"]["runner_script"]).exists()
    assert Path(res["master_summary_pdf"]).exists()


