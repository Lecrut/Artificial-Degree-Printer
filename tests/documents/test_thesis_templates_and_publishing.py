"""Thesis templates and publishing: thesis_plodz and paper_ieee, any number of chapters, the bundle with PDF, TeX and HTML, researchers by thesis type."""

from __future__ import annotations

from pathlib import Path

from adk.benchmarks import get_benchmark_task
from adk.mocks import code_fixtures as fx
from adk.mocks.scenarios import SCENARIOS
from adk.tools.building.output_bundle import (
    organize_benchmark_output_bundle,
    publish_workspace_thesis_bundle,
)
from adk.tools.building.template_manager import (
    copy_template_assets,
    render_template_latex,
    resolve_template_name,
)
from adk.tools.verification.ref_compiler import compile_symbolic_references


def test_list_and_resolve_templates(tmp_path: Path):
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

    config_src = "".join(code for _, code in fx.ANOMALY_CONFIG_AST_NODES)
    (ws / "config.py").write_text(config_src, encoding="utf-8")
    (ws / "results.csv").write_text(fx.ANOMALY_INITIAL_CSV, encoding="utf-8")
    (ws / "references.bib").write_text(fx.ANOMALY_BIBTEX, encoding="utf-8")

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

    config_src = "".join(code for _, code in fx.ANOMALY_CONFIG_AST_NODES)
    (ws / "config.py").write_text(config_src, encoding="utf-8")
    (ws / "results.csv").write_text(fx.ANOMALY_INITIAL_CSV, encoding="utf-8")
    (ws / "references.bib").write_text(fx.ANOMALY_BIBTEX, encoding="utf-8")
    (ws / "figures").mkdir()
    (ws / "figures" / "comparison_chart.png").write_bytes(b"PNG")  # a figure the experiment produced

    tex_path = render_template_latex(spec=spec, workspace_dir=ws, template_name="paper_ieee")
    assert tex_path.exists()
    assert (ws / "IEEEtran.cls").exists()

    content = tex_path.read_text(encoding="utf-8")
    assert "\\documentclass[conference]{IEEEtran}" in content
    assert "\\title{" in content
    assert "\\IEEEauthorblockN{" in content
    assert "\\begin{IEEEkeywords}" in content
    assert "\\bibliographystyle{IEEEtran}" in content
    assert "\\pagestyle{plain}" in content
    assert "\\thispagestyle{plain}" in content
    assert "figures/comparison_chart.png" in content

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
    (ws_plodz / "config.py").write_text("".join(c for _, c in fx.TICTACTOE_CONFIG_AST_NODES), encoding="utf-8")
    (ws_plodz / "core.py").write_text(fx.TICTACTOE_CORE_CODE, encoding="utf-8")
    (ws_plodz / "test_core.py").write_text(fx.TICTACTOE_TEST_CODE, encoding="utf-8")
    (ws_plodz / "plot_results.py").write_text(fx.TICTACTOE_PLOT_SCRIPT, encoding="utf-8")
    (ws_plodz / "references.bib").write_text(fx.TICTACTOE_BIBTEX, encoding="utf-8")
    (ws_plodz / "thesis.md").write_text(f"## {fx.TICTACTOE_DOC_SECTION_TITLE}\n{fx.TICTACTOE_DOC_SECTION_CONTENT}\n", encoding="utf-8")

    pub_plodz = publish_workspace_thesis_bundle(
        spec=spec,
        workspace_dir=ws_plodz,
        template_name="thesis_plodz",
        entrypoint="core.py:train_and_evaluate",
        plots="plot_results.py:generate_plots",
    )
    assert pub_plodz["symbolic_status"] == "PASS"
    assert pub_plodz["tex_symbolic_status"] == "PASS"
    assert (ws_plodz / "thesis" / "ThesisPLodz.cls").exists()
    assert (ws_plodz / "thesis" / "thesis.tex").exists()
    assert "ThesisPLodz" in (ws_plodz / "thesis" / "thesis.tex").read_text(encoding="utf-8")

    # 2. Test bundle with IEEEtran scientific paper template
    ws_paper = tmp_path / "bundle_paper"
    ws_paper.mkdir(parents=True, exist_ok=True)
    (ws_paper / "config.py").write_text("".join(c for _, c in fx.TICTACTOE_CONFIG_AST_NODES), encoding="utf-8")
    (ws_paper / "core.py").write_text(fx.TICTACTOE_CORE_CODE, encoding="utf-8")
    (ws_paper / "test_core.py").write_text(fx.TICTACTOE_TEST_CODE, encoding="utf-8")
    (ws_paper / "plot_results.py").write_text(fx.TICTACTOE_PLOT_SCRIPT, encoding="utf-8")
    (ws_paper / "references.bib").write_text(fx.TICTACTOE_BIBTEX, encoding="utf-8")
    (ws_paper / "thesis.md").write_text(f"## {fx.TICTACTOE_DOC_SECTION_TITLE}\n{fx.TICTACTOE_DOC_SECTION_CONTENT}\n", encoding="utf-8")

    pub_paper = publish_workspace_thesis_bundle(
        spec=spec,
        workspace_dir=ws_paper,
        template_name="paper_ieee",
        thesis_type="paper",
        entrypoint="core.py:train_and_evaluate",
        plots="plot_results.py:generate_plots",
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


def test_two_researchers_and_three_tier_routing():
    """Verify 2-researcher architecture (background_researcher & discoverer_researcher) and 3-tier routing."""
    from adk.benchmarks import BENCHMARK_TASKS
    from adk.core.models import read_json_state
    from adk.mocks.agents import SimulatedAgents
    from adk.mocks.scenarios import SCENARIOS

    reg_path = Path(__file__).resolve().parent.parent.parent / "adk" / "state" / "agent_registry.json"
    agents = read_json_state(reg_path)["agents"]
    assert agents["background_researcher"]["active"] is True
    assert agents["discoverer_researcher"]["active"] is True

    def _research(key: str) -> list[str]:
        """The researchers of the derived queue (§XVI) for the benchmark's document type."""
        from adk.orchestration.plan_outline import outline_of
        from adk.orchestration.plan_tasks import planned_tasks

        spec = BENCHMARK_TASKS[key]
        outline = outline_of(SimulatedAgents(SCENARIOS[key])("plan_outline", "", {"user_prompt": "x"}, "LRM"))
        tasks = planned_tasks(outline, SCENARIOS[key].interfaces(), spec.thesis_type, True, set())
        return [t["assigned_agent"] for t in tasks if "researcher" in t["assigned_agent"]]

    assert _research("01_rl_tictactoe") == ["background_researcher"]
    assert _research("02_ml_anomaly_detection") == ["background_researcher", "discoverer_researcher"]
    for key in ("03_graph_pathfinding", "04_federated_learning"):
        assert _research(key) == ["discoverer_researcher"]


def test_detect_template_from_prompt_and_live_mock_isolation(tmp_path: Path):
    """Verify automatic template detection, uncertainty question when ambiguous, and zero mock injection in live runs."""
    from adk.benchmarks import BENCHMARK_TASKS
    from adk.orchestrator import NeuroSymbolicOrchestrator
    from adk.tools.building.template_manager import detect_template_from_prompt

    # 1. All 4 benchmark prompts explicitly specify their template and thesis_type
    d1 = detect_template_from_prompt(BENCHMARK_TASKS["01_rl_tictactoe"].prompt)
    assert d1["is_certain"] is True
    assert d1["thesis_type"] == "inzynierska"
    assert d1["template_name"] == "thesis_plodz"

    d2 = detect_template_from_prompt(BENCHMARK_TASKS["02_ml_anomaly_detection"].prompt)
    assert d2["is_certain"] is True
    assert d2["thesis_type"] == "magisterska"
    assert d2["template_name"] == "thesis_plodz"

    d3 = detect_template_from_prompt(BENCHMARK_TASKS["03_graph_pathfinding"].prompt)
    assert d3["is_certain"] is True
    assert d3["thesis_type"] == "paper"
    assert d3["template_name"] == "paper_ieee"

    d4 = detect_template_from_prompt(BENCHMARK_TASKS["04_federated_learning"].prompt)
    assert d4["is_certain"] is True
    assert d4["thesis_type"] == "paper"
    assert d4["template_name"] == "paper_ieee"

    # 2. Ambiguous prompt without template indicators triggers uncertainty and question
    d_ambig = detect_template_from_prompt("Zaimplementuj algorytm sortowania w Pythonie i opisz wyniki.")
    assert d_ambig["is_certain"] is False
    assert d_ambig["question"] is not None
    assert "thesis_plodz" in d_ambig["question"]
    assert "paper_ieee" in d_ambig["question"]

    # 4. Live provider mode never injects Tic-Tac-Toe mock code or mock chapters
    orch = NeuroSymbolicOrchestrator(adk_root=tmp_path / "live_adk", provider="ollama")
    orch.workspace_dir.mkdir(parents=True, exist_ok=True)
    orch._materialize_workspace_artifact("config.py", {})
    assert not (orch.workspace_dir / "config.py").exists()
    orch._materialize_workspace_artifact(
        "thesis.md",
        {
            "sections": [
                {
                    "section_title": "Autorski Rozdział LLM",
                    "section_content": "Własna treść wygenerowana przez model językowy.\n\n### Podrozdział 1\nAnaliza szczegółowa.",
                }
            ]
        },
    )
    # A shape outside the output schema is reported back to the agent instead of being guessed at or dropped.
    import pytest

    from adk.orchestrator import MaterializationError

    with pytest.raises(MaterializationError):
        orch._materialize_workspace_artifact("thesis.md", {"chapter": {"title": "X", "content": "Y"}})
    assert not (orch.workspace_dir / "results.csv").exists()
    md_text = (orch.workspace_dir / "thesis.md").read_text(encoding="utf-8")
    assert "Autorski Rozdział LLM" in md_text
    assert "Tic-Tac-Toe" not in md_text


def test_dynamic_arbitrary_chapter_counts_in_latex_rendering(tmp_path: Path):
    """Verify that template_manager dynamically supports arbitrary chapter counts (e.g. 10 chapters or 4 sections) without truncation or crash."""
    spec = get_benchmark_task("01_rl_tictactoe")

    # 1. Test 10 chapters in thesis_plodz
    ws_10 = tmp_path / "ws_10_chapters"
    ws_10.mkdir(parents=True, exist_ok=True)
    config_src = "".join(code for _, code in fx.TICTACTOE_CONFIG_AST_NODES)
    (ws_10 / "config.py").write_text(config_src, encoding="utf-8")
    (ws_10 / "results.csv").write_text(fx.TICTACTOE_INITIAL_CSV, encoding="utf-8")
    (ws_10 / "references.bib").write_text(fx.TICTACTOE_BIBTEX, encoding="utf-8")

    md_10_content = "\n\n".join(
        f"## Rozdział {i}: Dziedzinowa sekcja numer {i}\nTreść rozdziału {i} ze wskaźnikiem \\ref_ast{{config.py:ALPHA}} i wynikiem \\ref_csv{{results.csv:proposed+win_rate:value}}."
        for i in range(1, 11)
    )
    (ws_10 / "thesis.md").write_text(md_10_content, encoding="utf-8")

    tex_10 = render_template_latex(spec=spec, workspace_dir=ws_10, template_name="thesis_plodz")
    assert tex_10.exists()
    tex_10_content = tex_10.read_text(encoding="utf-8")

    # Must contain all 10 \chapter directives!
    for i in range(1, 11):
        assert f"\\chapter{{Rozdział {i}: Dziedzinowa sekcja numer {i}}}" in tex_10_content

    # Verify symbolic compilation passes
    comp_10 = compile_symbolic_references(tex_10, ws_10, write_compiled=True)
    assert comp_10["status"] == "PASS"

    # 2. Test 4 sections in paper_ieee
    ws_4 = tmp_path / "ws_4_sections"
    ws_4.mkdir(parents=True, exist_ok=True)
    (ws_4 / "config.py").write_text(config_src, encoding="utf-8")
    (ws_4 / "results.csv").write_text(fx.TICTACTOE_INITIAL_CSV, encoding="utf-8")
    (ws_4 / "references.bib").write_text(fx.TICTACTOE_BIBTEX, encoding="utf-8")

    md_4_content = "\n\n".join(
        f"## Section {i}: Focused Paper Segment {i}\nDetailed methodology segment {i} using \\ref_ast{{config.py:GAMMA}}."
        for i in range(1, 5)
    )
    (ws_4 / "thesis.md").write_text(md_4_content, encoding="utf-8")

    tex_4 = render_template_latex(spec=spec, workspace_dir=ws_4, template_name="paper_ieee")
    assert tex_4.exists()
    tex_4_content = tex_4.read_text(encoding="utf-8")

    # Must contain all 4 \section directives and no phantom sections
    for i in range(1, 5):
        assert f"\\section{{Section {i}: Focused Paper Segment {i}}}" in tex_4_content
    assert "\\section{Section 5" not in tex_4_content

    comp_4 = compile_symbolic_references(tex_4, ws_4, write_compiled=True)
    assert comp_4["status"] == "PASS"


def test_the_published_bundle_keeps_package_code(tmp_path: Path) -> None:
    """R1: only root files were copied, so 02's `code/` was empty while its code sat in `src/`."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "detector.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "main_entry.py").write_text("y = 2\n", encoding="utf-8")
    (tmp_path / "evolved_adk" / "tools").mkdir(parents=True)
    (tmp_path / "evolved_adk" / "tools" / "t.py").write_text("z = 3\n", encoding="utf-8")
    organize_benchmark_output_bundle(tmp_path)
    assert (tmp_path / "code" / "src" / "detector.py").is_file()
    assert (tmp_path / "code" / "main_entry.py").is_file()
    assert not (tmp_path / "src").exists()
    assert (tmp_path / "evolved_adk" / "tools" / "t.py").is_file()


def test_thesis_publisher_generates_pdf_tex_html_and_runner(tmp_path: Path):
    """Verify that publish_workspace_thesis_bundle executes code, generates plots, compiles refs, and writes valid PDF/LaTeX/HTML."""
    spec = get_benchmark_task("02_ml_anomaly_detection")
    ws = tmp_path / "anomaly_ws"
    ws.mkdir(parents=True, exist_ok=True)

    # Seed workspace files for task 2 with what its simulated agents would have written
    sc = SCENARIOS["02_ml_anomaly_detection"]
    (ws / "config.py").write_text("".join(code for _, code in sc.config_ast_nodes), encoding="utf-8")
    (ws / "core.py").write_text(sc.core_code, encoding="utf-8")
    (ws / "test_core.py").write_text(sc.test_code, encoding="utf-8")
    (ws / "plot_results.py").write_text(sc.plot_script, encoding="utf-8")
    (ws / "references.bib").write_text(sc.background_bibtex + "\n" + sc.discoverer_bibtex, encoding="utf-8")
    (ws / "thesis.md").write_text("".join(f"## {t}\n{c}\n\n" for t, c in sc.thesis_chapters), encoding="utf-8")

    pub = publish_workspace_thesis_bundle(
        spec=spec,
        workspace_dir=ws,
        evolution_summary={"events_triggered": ["CREATE_AGENT", "SPLIT_AGENT"], "active_agents_count": 6, "elapsed_seconds": 0.42},
        entrypoint="core.py:train_and_evaluate",
        plots="plot_results.py:generate_plots",
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
