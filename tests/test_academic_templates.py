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
    assert "\\pagestyle{plain}" in content
    assert "\\thispagestyle{plain}" in content
    assert "width=\\columnwidth,keepaspectratio" in content
    assert "\\pagestyle{plain}" in content
    assert "\\thispagestyle{plain}" in content
    assert "width=\\columnwidth,keepaspectratio" in content

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


def test_two_researchers_and_three_tier_routing():
    """Verify 2-researcher architecture (background_researcher & discoverer_researcher) and 3-tier routing."""
    from adk.benchmarks import BENCHMARK_TASKS
    from adk.benchmarks.runner import _make_task_mock_llm_handler
    from adk.core.models import read_json_state
    from adk.orchestrator import _merge_bibtex_entries

    # 1. Verify both researchers are active in agent_registry.json
    reg_path = Path(__file__).resolve().parent.parent / "adk" / "state" / "agent_registry.json"
    agents = read_json_state(reg_path)["agents"]
    assert agents["background_researcher"]["active"] is True
    assert agents["discoverer_researcher"]["active"] is True

    # 2. Verify Tier I (inzynierska -> background_researcher only)
    h1 = _make_task_mock_llm_handler(BENCHMARK_TASKS["01_rl_tictactoe"])
    plan1 = h1("Task Planner", {"user_prompt": "x", "blast_radius": {}}, "LRM")
    research_agents_1 = [
        t["assigned_agent"]
        for t in plan1["tasks"]
        if "researcher" in t["assigned_agent"]
    ]
    assert research_agents_1 == ["background_researcher"]

    # 3. Verify Tier II (magisterska -> background_researcher THEN discoverer_researcher)
    h2 = _make_task_mock_llm_handler(BENCHMARK_TASKS["02_ml_anomaly_detection"])
    plan2 = h2("Task Planner", {"user_prompt": "x", "blast_radius": {}}, "LRM")
    research_agents_2 = [
        t["assigned_agent"]
        for t in plan2["tasks"]
        if "researcher" in t["assigned_agent"]
    ]
    assert research_agents_2 == ["background_researcher", "discoverer_researcher"]

    # 4. Verify Tier III (paper -> discoverer_researcher only)
    for key in ("03_graph_pathfinding", "04_federated_learning"):
        h3 = _make_task_mock_llm_handler(BENCHMARK_TASKS[key])
        plan3 = h3("Task Planner", {"user_prompt": "x", "blast_radius": {}}, "LRM")
        research_agents_3 = [
            t["assigned_agent"]
            for t in plan3["tasks"]
            if "researcher" in t["assigned_agent"]
        ]
        assert research_agents_3 == ["discoverer_researcher"]

    # 5. Verify BibTeX merging preserves both background and discoverer entries without duplicates
    spec2 = BENCHMARK_TASKS["02_ml_anomaly_detection"]
    merged = _merge_bibtex_entries(spec2.background_bibtex_entries, spec2.discoverer_bibtex_entries)
    assert "hampel1974influence" in merged
    assert "liu2008isolation" in merged
    assert "xu2023deep" in merged
    assert "zhang2024conformal" in merged


def test_detect_template_from_prompt_and_live_mock_isolation(tmp_path: Path):
    """Verify automatic template detection, uncertainty question when ambiguous, and zero mock injection in live runs."""
    from adk.benchmarks import BENCHMARK_TASKS
    from adk.mocks import _make_task_mock_llm_handler, render_thesis_pdf
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

    # 3. Mocks and mock PDF template are isolated in adk.mocks
    assert render_thesis_pdf.__module__ == "adk.mocks.mock_pdf_template"
    assert _make_task_mock_llm_handler.__module__ == "adk.mocks.benchmark_mock_handlers"

    # 4. Live provider mode never injects Tic-Tac-Toe mock code or mock chapters
    orch = NeuroSymbolicOrchestrator(adk_root=tmp_path / "live_adk", provider="ollama")
    orch.workspace_dir.mkdir(parents=True, exist_ok=True)
    orch._materialize_workspace_artifact("config.py", {})
    assert not (orch.workspace_dir / "config.py").exists()
    orch._materialize_workspace_artifact(
        "thesis.md",
        {
            "chapter": {
                "title": "Autorski Rozdział LLM",
                "content": "Własna treść wygenerowana przez model językowy.",
                "subsections": [{"heading": "Podrozdział 1", "content": "Analiza szczegółowa."}],
            }
        },
    )
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
    config_src = "".join(code for _, code in spec.config_ast_nodes)
    (ws_10 / "config.py").write_text(config_src, encoding="utf-8")
    (ws_10 / "results.csv").write_text(spec.initial_csv, encoding="utf-8")
    (ws_10 / "references.bib").write_text(spec.bibtex_entries, encoding="utf-8")

    md_10_content = "\n\n".join(
        f"## Rozdział {i}: Dziedzinowa sekcja numer {i}\nTreść rozdziału {i} ze wskaźnikiem \\ref_ast{{config.py:ALPHA}} i wynikiem \\ref_csv{{results.csv:win_rate}}."
        for i in range(1, 11)
    )
    (ws_10 / "thesis.md").write_text(md_10_content, encoding="utf-8")

    tex_10 = render_template_latex(spec=spec, workspace_dir=ws_10, template_name="thesis_plodz", provider="live")
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
    (ws_4 / "results.csv").write_text(spec.initial_csv, encoding="utf-8")
    (ws_4 / "references.bib").write_text(spec.bibtex_entries, encoding="utf-8")

    md_4_content = "\n\n".join(
        f"## Section {i}: Focused Paper Segment {i}\nDetailed methodology segment {i} using \\ref_ast{{config.py:GAMMA}}."
        for i in range(1, 5)
    )
    (ws_4 / "thesis.md").write_text(md_4_content, encoding="utf-8")

    tex_4 = render_template_latex(spec=spec, workspace_dir=ws_4, template_name="paper_ieee", provider="live")
    assert tex_4.exists()
    tex_4_content = tex_4.read_text(encoding="utf-8")

    # Must contain all 4 \section directives and no phantom sections
    for i in range(1, 5):
        assert f"\\section{{Section {i}: Focused Paper Segment {i}}}" in tex_4_content
    assert "\\section{Section 5" not in tex_4_content

    comp_4 = compile_symbolic_references(tex_4, ws_4, write_compiled=True)
    assert comp_4["status"] == "PASS"



