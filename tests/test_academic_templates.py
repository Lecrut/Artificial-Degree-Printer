from __future__ import annotations

from pathlib import Path

from adk.benchmarks import get_benchmark_task
from adk.tools.building.template_manager import (
    copy_template_assets,
    list_available_templates,
    render_template_latex,
    resolve_template_name,
)
from adk.tools.building.thesis_publisher import publish_workspace_thesis_bundle
from adk.tools.verification.ref_compiler import compile_symbolic_references


def test_list_and_resolve_templates(tmp_path: Path):
    templates = list_available_templates()
    assert "thesis_plodz" in templates
    assert "paper_ieee" in templates

    assert resolve_template_name(thesis_type="inzynierska") == "thesis_plodz"
    assert resolve_template_name(thesis_type="magisterska") == "thesis_plodz"
    assert resolve_template_name(thesis_type="engineering") == "thesis_plodz"
    assert resolve_template_name(thesis_type="paper") == "paper_ieee"
    assert resolve_template_name(thesis_type="article") == "paper_ieee"
    assert resolve_template_name(thesis_type="scientific_paper") == "paper_ieee"
    assert resolve_template_name(requested_template="thesis_plodz") == "thesis_plodz"
    assert resolve_template_name(requested_template="paper_ieee") == "paper_ieee"

    # Test copy assets
    copied = copy_template_assets("thesis_plodz", tmp_path / "assets_test")
    assert any(c.name == "ThesisPLodz.cls" for c in copied)


def test_thesis_plodz_template_rendering_and_compilation(tmp_path: Path):
    spec = get_benchmark_task("02_ml_anomaly_detection")
    ws = tmp_path / "plodz_ws"
    ws.mkdir(parents=True, exist_ok=True)

    config_src = "".join(code for _, code in spec.config_ast_nodes)
    (ws / "config.py").write_text(config_src, encoding="utf-8")
    (ws / "results.csv").write_text(spec.initial_csv, encoding="utf-8")
    (ws / "references.bib").write_text(spec.bibtex_entries, encoding="utf-8")

    tex_path = render_template_latex(spec=spec, workspace_dir=ws, template_name="thesis_plodz")
    assert tex_path.exists()
    assert (ws / "ThesisPLodz.cls").exists()

    content = tex_path.read_text(encoding="utf-8")
    assert "\\documentclass[W2, polski]{ThesisPLodz}" in content
    assert "\\authorname{" in content
    assert "\\studentnumber{" in content
    assert "\\thesistitle{" in content
    assert "\\degreename{magisterska}" in content
    assert "\\fieldofstudy{" in content
    assert "\\supervisor{" in content
    assert "\\symbolslist{" in content
    assert "\\abbreviationslist{" in content

    # Verify symbolic compilation
    comp = compile_symbolic_references(tex_path, ws, write_compiled=True)
    assert comp["status"] == "PASS"
    compiled_tex = ws / "thesis.compiled.tex"
    assert compiled_tex.exists()
    compiled_text = compiled_tex.read_text(encoding="utf-8")
    assert "\\ref_ast{" not in compiled_text
    assert "\\ref_csv{" not in compiled_text


def test_paper_ieee_template_rendering_and_compilation(tmp_path: Path):
    spec = get_benchmark_task("02_ml_anomaly_detection")
    ws = tmp_path / "paper_ws"
    ws.mkdir(parents=True, exist_ok=True)

    config_src = "".join(code for _, code in spec.config_ast_nodes)
    (ws / "config.py").write_text(config_src, encoding="utf-8")
    (ws / "results.csv").write_text(spec.initial_csv, encoding="utf-8")
    (ws / "references.bib").write_text(spec.bibtex_entries, encoding="utf-8")

    tex_path = render_template_latex(spec=spec, workspace_dir=ws, template_name="paper_ieee")
    assert tex_path.exists()
    assert (ws / "IEEEtran.cls").exists()

    content = tex_path.read_text(encoding="utf-8")
    assert "\\documentclass[conference]{IEEEtran}" in content
    assert "\\title{" in content
    assert "\\IEEEauthorblockN{" in content
    assert "\\begin{IEEEkeywords}" in content
    assert "\\bibliographystyle{IEEEtran}" in content

    # Verify symbolic compilation
    comp = compile_symbolic_references(tex_path, ws, write_compiled=True)
    assert comp["status"] == "PASS"
    compiled_tex = ws / "thesis.compiled.tex"
    assert compiled_tex.exists()
    compiled_text = compiled_tex.read_text(encoding="utf-8")
    assert "\\ref_ast{" not in compiled_text
    assert "\\ref_csv{" not in compiled_text


def test_publish_bundle_with_both_templates(tmp_path: Path):
    spec = get_benchmark_task("01_rl_tictactoe")

    # 1. Test bundle with Politechnika Łódzka template
    ws_plodz = tmp_path / "bundle_plodz"
    ws_plodz.mkdir(parents=True, exist_ok=True)
    (ws_plodz / "config.py").write_text("".join(c for _, c in spec.config_ast_nodes), encoding="utf-8")
    (ws_plodz / "core.py").write_text(spec.core_code, encoding="utf-8")
    (ws_plodz / "test_core.py").write_text(spec.test_code, encoding="utf-8")
    (ws_plodz / "plot_results.py").write_text(spec.plot_script, encoding="utf-8")
    (ws_plodz / "references.bib").write_text(spec.bibtex_entries, encoding="utf-8")
    (ws_plodz / "thesis.md").write_text(f"## {spec.doc_section_title}\n{spec.doc_section_content}\n", encoding="utf-8")

    pub_plodz = publish_workspace_thesis_bundle(
        spec=spec,
        workspace_dir=ws_plodz,
        template_name="thesis_plodz",
    )
    assert pub_plodz["symbolic_status"] == "PASS"
    assert pub_plodz["tex_symbolic_status"] == "PASS"
    assert (ws_plodz / "thesis" / "ThesisPLodz.cls").exists()
    assert (ws_plodz / "thesis" / "thesis.tex").exists()
    assert "ThesisPLodz" in (ws_plodz / "thesis" / "thesis.tex").read_text(encoding="utf-8")

    # 2. Test bundle with IEEEtran scientific paper template
    ws_paper = tmp_path / "bundle_paper"
    ws_paper.mkdir(parents=True, exist_ok=True)
    (ws_paper / "config.py").write_text("".join(c for _, c in spec.config_ast_nodes), encoding="utf-8")
    (ws_paper / "core.py").write_text(spec.core_code, encoding="utf-8")
    (ws_paper / "test_core.py").write_text(spec.test_code, encoding="utf-8")
    (ws_paper / "plot_results.py").write_text(spec.plot_script, encoding="utf-8")
    (ws_paper / "references.bib").write_text(spec.bibtex_entries, encoding="utf-8")
    (ws_paper / "thesis.md").write_text(f"## {spec.doc_section_title}\n{spec.doc_section_content}\n", encoding="utf-8")

    pub_paper = publish_workspace_thesis_bundle(
        spec=spec,
        workspace_dir=ws_paper,
        template_name="paper_ieee",
        thesis_type="paper",
    )
    assert pub_paper["symbolic_status"] == "PASS"
    assert pub_paper["tex_symbolic_status"] == "PASS"
    assert (ws_paper / "thesis" / "IEEEtran.cls").exists()
    assert (ws_paper / "thesis" / "thesis.tex").exists()
    assert "IEEEtran" in (ws_paper / "thesis" / "thesis.tex").read_text(encoding="utf-8")


def test_benchmark_tasks_use_distinct_thesis_types(tmp_path: Path):
    """Verify that benchmarks cover inżynierska, magisterska, and artykuł naukowy (IEEE)."""
    from adk.benchmarks import BENCHMARK_TASKS

    t1 = BENCHMARK_TASKS["01_rl_tictactoe"]
    assert t1.thesis_type == "inzynierska"
    assert t1.template_name == "thesis_plodz"
    ws1 = tmp_path / "ws1"
    ws1.mkdir()
    p1 = render_template_latex(t1, ws1)
    content1 = p1.read_text(encoding="utf-8")
    assert "\\documentclass[W2, polski]{ThesisPLodz}" in content1
    assert "\\degreename{inzynierska}" in content1

    t2 = BENCHMARK_TASKS["02_ml_anomaly_detection"]
    assert t2.thesis_type == "magisterska"
    assert t2.template_name == "thesis_plodz"
    ws2 = tmp_path / "ws2"
    ws2.mkdir()
    p2 = render_template_latex(t2, ws2)
    content2 = p2.read_text(encoding="utf-8")
    assert "\\documentclass[W2, polski]{ThesisPLodz}" in content2
    assert "\\degreename{magisterska}" in content2

    t3 = BENCHMARK_TASKS["03_graph_pathfinding"]
    assert t3.thesis_type == "paper"
    assert t3.template_name == "paper_ieee"
    ws3 = tmp_path / "ws3"
    ws3.mkdir()
    p3 = render_template_latex(t3, ws3)
    content3 = p3.read_text(encoding="utf-8")
    assert "\\documentclass[conference]{IEEEtran}" in content3

    t4 = BENCHMARK_TASKS["04_federated_learning"]
    assert t4.thesis_type == "paper"
    assert t4.template_name == "paper_ieee"
    ws4 = tmp_path / "ws4"
    ws4.mkdir()
    p4 = render_template_latex(t4, ws4)
    content4 = p4.read_text(encoding="utf-8")
    assert "\\documentclass[conference]{IEEEtran}" in content4
