from __future__ import annotations

import json
from pathlib import Path

from adk.core.llm import _extract_json_from_text, call_agent
from adk.tools.planning import (
    calculate_blast_radius,
    escalate_node_weight,
    get_scoped_hypergraph_context,
    scout_domain_conventions,
    select_model_tier,
    synthesize_table_of_contents,
)



def test_state_files_initialized():
    root = Path(__file__).resolve().parent.parent / "adk" / "state"
    expected = [
        "hypergraph_matrix.json",
        "task_queue.json",
        "agent_registry.json",
        "validation_report.json",
        "failure_ledger.json",
        "evolution_history.json",
        "hitl_flag.json",
    ]
    for filename in expected:
        file_path = root / filename
        assert file_path.exists(), f"Missing state file: {filename}"
        data = json.loads(file_path.read_text(encoding="utf-8"))
        assert data is not None


def test_blast_radius_and_complexity_router(tmp_path: Path):
    # The repository seed is empty (the graph is built from files), so this test brings its own graph.
    matrix_path = tmp_path / "hypergraph_matrix.json"
    matrix_path.write_text(
        json.dumps(
            {
                "nodes": {
                    "v1": {"path": "config.py", "degree": 2, "weight": 1.4},
                    "v2": {"path": "core.py", "degree": 3, "weight": 1.2},
                    "v3": {"path": "results.csv", "degree": 2, "weight": 1.4},
                    "v4": {"path": "thesis.md", "degree": 1, "weight": 9.2},
                },
                "edges": {"E1": ["v1", "v2"], "E2": ["v2", "v3"], "E3": ["v1", "v3", "v4"]},
                "matrix": {
                    "v1": {"E1": 1, "E2": 0, "E3": 1},
                    "v2": {"E1": 1, "E2": 1, "E3": 0},
                    "v3": {"E1": 0, "E2": 1, "E3": 1},
                    "v4": {"E1": 0, "E2": 0, "E3": 1},
                },
            }
        ),
        encoding="utf-8",
    )
    res = calculate_blast_radius("v1", matrix_path)
    assert res["degree"] >= 2
    assert "E1" in res["active_edges"]
    assert "v2" in res["affected_nodes"]

    assert select_model_tier("v1", matrix_path) == "LRM"
    assert select_model_tier("v4", matrix_path) == "LRM"

    # Unknown node robustness: select_model_tier returns LRM fallback and does not raise KeyError
    assert select_model_tier("v7", matrix_path) == "LRM"
    assert select_model_tier("core.py", matrix_path) in ("LRM", "SML")

    # Unknown node in calculate_blast_radius returns safe fallback dict
    blast_unknown = calculate_blast_radius("v7", matrix_path)
    assert blast_unknown["modified_node_id"] == "v7"
    assert blast_unknown["degree"] == 0
    assert "v7" in blast_unknown["affected_nodes"]


def test_call_planning_agents():
    planner_res = call_agent(
        "agents/planning/task_planner.md",
        {"user_prompt": "Create config validation"},
        model_tier="LRM",
        provider="mock",
    )
    assert planner_res["status"] == "ok"
    assert len(planner_res["output"]["tasks"]) >= 1

    guard_res = call_agent(
        "agents/planning/task_critic_guard.md",
        {
            "tasks": planner_res["output"]["tasks"],
            "agent_registry": {
                "agents": {
                    "seed_coder": {"active": True},
                    "seed_tester": {"active": True},
                    "seed_writer": {"active": True},
                }
            },
        },
        model_tier="SML",
        provider="mock",
    )
    assert guard_res["output"]["status"] == "PASS"


def test_robust_json_extraction_with_think_tags_and_prose():
    noisy_output = (
        "<think>\nLet me analyze the hypergraph blast radius first.\n</think>\n"
        "Here is the required JSON output:\n"
        "```json\n"
        '{"status": "PASS", "approved": true, "issues": []}\n'
        "```\n"
        "Hope this helps!"
    )
    parsed = _extract_json_from_text(noisy_output)
    assert isinstance(parsed, dict)
    assert parsed["status"] == "PASS"
    assert parsed["approved"] is True


def test_evoroute_escalate_node_weight_switches_sml_to_lrm(tmp_path: Path):
    matrix_file = tmp_path / "hypergraph_matrix.json"
    matrix_file.write_text(
        json.dumps(
            {
                "nodes": {
                    "v5": {"path": "test_core.py", "degree": 1, "weight": 1.0},
                },
                "edges": {"E4": ["v5"]},
                "matrix": {"v5": {"E4": 1}},
            }
        ),
        encoding="utf-8",
    )

    assert select_model_tier("v5", matrix_file) == "SML"

    esc1 = escalate_node_weight("v5", delta=0.4, matrix_path=matrix_file)
    assert esc1["old_weight"] == 1.0
    assert esc1["new_weight"] == 1.4
    assert esc1["new_tier"] == "SML"

    esc2 = escalate_node_weight("v5", delta=0.4, matrix_path=matrix_file)
    assert esc2["old_weight"] == 1.4
    assert esc2["new_weight"] == 1.8
    assert esc2["new_tier"] == "LRM"
    assert select_model_tier("v5", matrix_file) == "LRM"


def test_get_scoped_hypergraph_context_omits_matrix_and_scopes_edges(tmp_path: Path):
    # Simulate a hypergraph with 100 edges and heavy 0/1 incidence matrix
    edges = {f"E{i}": [f"v{i % 5 + 1}"] for i in range(1, 101)}
    edges["E1"] = ["v1", "v2"]
    nodes = {f"v{i}": {"path": f"module_{i}.py", "degree": i, "weight": 1.0} for i in range(1, 6)}
    matrix = {n_id: {e_id: 1 if n_id in members else 0 for e_id, members in edges.items()} for n_id, members in [(f"v{i}", edges) for i in range(1, 6)]}
    
    matrix_file = tmp_path / "heavy_matrix.json"
    matrix_file.write_text(json.dumps({"nodes": nodes, "edges": edges, "matrix": matrix}), encoding="utf-8")

    blast = calculate_blast_radius("v1", matrix_file)
    scoped = get_scoped_hypergraph_context(matrix_file, blast_radius=blast)

    assert "matrix" not in scoped
    assert "nodes" in scoped
    assert "active_edges" in scoped
    assert "v1" in scoped["nodes"]
    assert "E1" in scoped["active_edges"]
    # Only active edges related to blast radius should be present, not all 100
    assert len(scoped["active_edges"]) < len(edges)


def test_scout_domain_conventions_and_synthesize_toc():
    """Verify Layer 1 research reconnaissance and dynamic Table-of-Contents (TOC) synthesis tools."""
    # 1. Stage I (Inżynierska) reconnaissance & TOC
    recon_rl = scout_domain_conventions("01_rl_tictactoe", thesis_type="inzynierska")
    assert recon_rl["task_key"] == "01_rl_tictactoe"
    assert recon_rl["research_routing"] == ["background_researcher"]
    assert len(recon_rl["canonical_baselines"]) >= 3
    assert "win_rate" in recon_rl["standard_metrics"]
    assert len(recon_rl["available_citation_keys"]) >= 20

    toc_rl = synthesize_table_of_contents("01_rl_tictactoe", thesis_type="inzynierska", recon_report=recon_rl)
    chapters_rl = toc_rl["chapters"]
    assert len(chapters_rl) == 6
    assert chapters_rl[1]["chapter_index"] == 2
    assert chapters_rl[1]["assigned_agent"] == "background_researcher"
    assert len(chapters_rl[1]["subsections"]) >= 3

    # 2. Stage II (Magisterska) reconnaissance & TOC
    recon_anom = scout_domain_conventions("02_ml_anomaly_detection", thesis_type="magisterska")
    assert recon_anom["task_key"] == "02_ml_anomaly_detection"
    assert recon_anom["research_routing"] == ["background_researcher", "discoverer_researcher"]
    assert "f1_score" in recon_anom["standard_metrics"]
    assert len(recon_anom["available_citation_keys"]) >= 30

    toc_anom = synthesize_table_of_contents("02_ml_anomaly_detection", thesis_type="magisterska", recon_report=recon_anom)
    chapters_anom = toc_anom["chapters"]
    assert len(chapters_anom) == 6
    assert chapters_anom[1]["assigned_agent"] == "background_researcher + discoverer_researcher"

    # 3. Stage III (Paper) reconnaissance & TOC
    recon_fl = scout_domain_conventions("04_federated_learning", thesis_type="paper")
    assert recon_fl["task_key"] == "04_federated_learning"
    assert recon_fl["research_routing"] == ["discoverer_researcher"]
    assert "final_accuracy" in recon_fl["standard_metrics"]

    toc_fl = synthesize_table_of_contents("04_federated_learning", thesis_type="paper", recon_report=recon_fl)
    chapters_fl = toc_fl["chapters"]
    assert len(chapters_fl) == 6
    assert chapters_fl[1]["assigned_agent"] == "discoverer_researcher"
    assert "Related Work" in chapters_fl[1]["chapter_title"]


def test_research_first_task_ordering_in_planner():
    """Verify that Task Planner schedules Literature Research FIRST (on v4) before config (v1), core (v2), tests (v3), and thesis writer (v4)."""
    from adk.benchmarks import BENCHMARK_TASKS
    from adk.benchmarks.runner import _make_task_mock_llm_handler

    for task_id, spec in BENCHMARK_TASKS.items():
        handler = _make_task_mock_llm_handler(spec)
        plan_out = handler("Task Planner", {"user_prompt": spec.prompt, "blast_radius": {}}, "LRM")
        tasks = plan_out["tasks"]
        blueprint = plan_out["academic_blueprint"]

        # Blueprint must include literature_recon and 6-chapter table_of_contents
        assert "literature_recon" in blueprint
        assert "table_of_contents" in blueprint
        assert len(blueprint["table_of_contents"]["chapters"]) == 6

        # First task must ALWAYS be a researcher on v4 (Research-First workflow)
        first_task = tasks[0]
        assert first_task["target_node"] == "v4", f"First task in {task_id} must target v4 (research first)"
        assert "researcher" in first_task["assigned_agent"], f"First task in {task_id} must be assigned to a researcher"

        # Last task must ALWAYS be seed_writer on v4 (final thesis synthesis)
        last_task = tasks[-1]
        assert last_task["target_node"] == "v4"
        assert last_task["assigned_agent"] == "seed_writer"


def test_paper_card_extraction_and_arxiv_openalex_parsers():
    """Verify dynamic PaperCard extraction from arXiv Atom XML and OpenAlex inverted-index JSON."""
    from adk.tools.building.literature_engine import (
        _parse_arxiv_atom_xml,
        _parse_openalex_json,
        _reconstruct_openalex_abstract,
        extract_paper_card_from_abstract,
        fetch_live_or_curated_papers,
        format_bibtex,
    )

    card = extract_paper_card_from_abstract(
        title="Adaptive Proximal Federated Optimization under Non-IID Drift",
        abstract=(
            "We propose a novel adaptive proximal regularizer for federated learning. "
            "Experiments on the CIFAR-10 and LEAF benchmark datasets show 94.2% accuracy and 1.8x speedup. "
            "However, a key limitation is the quadratic memory overhead when storing full client histories."
        ),
        authors=["Kowalski, Jan", "Nowak, Anna"],
        year="2025",
        venue="ICML",
        stage="discoverer",
    )
    assert card["key"].startswith("kowalski2025")
    assert "propose" in card["methodology"].lower()
    assert "benchmark" in card["dataset"].lower()
    assert "94.2%" in card["reported_metrics"]
    assert "limitation" in card["limitation"].lower()
    bib = format_bibtex(card)
    assert f"@article{{{card['key']}," in bib

    # Test arXiv Atom XML parser
    sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <title>Symbolic Verification of Neural Policies</title>
        <summary>We introduce an AST-grounded symbolic verifier evaluated on grid benchmarks achieving 99.1% accuracy. However, solver timeouts remain a bottleneck.</summary>
        <published>2024-06-15T00:00:00Z</published>
        <author><name>Elena Rostova</name></author>
      </entry>
    </feed>"""
    arxiv_cards = _parse_arxiv_atom_xml(sample_xml, stage="discoverer")
    assert len(arxiv_cards) == 1
    assert arxiv_cards[0]["key"].startswith("rostova2024")
    assert "99.1%" in arxiv_cards[0]["reported_metrics"]

    # Test OpenAlex inverted-index reconstruction and JSON parser
    inv_idx = {"We": [0], "propose": [1], "robust": [2], "subspace": [3], "ensembles": [4], "with": [5], "96.5%": [6], "F1.": [7]}
    assert _reconstruct_openalex_abstract(inv_idx) == "We propose robust subspace ensembles with 96.5% F1."

    oa_payload = {
        "results": [
            {
                "title": "Robust Subspace Ensembles for Physiological Telemetry",
                "publication_year": 2024,
                "cited_by_count": 42,
                "authorships": [{"author": {"display_name": "Piotr Wiśniewski"}}],
                "primary_location": {"source": {"display_name": "IEEE JBHI"}},
                "abstract_inverted_index": inv_idx,
            }
        ]
    }
    oa_cards = _parse_openalex_json(oa_payload, stage="discoverer")
    assert len(oa_cards) == 1
    assert oa_cards[0]["venue"] == "IEEE JBHI"
    assert "96.5%" in oa_cards[0]["reported_metrics"]

    curated = fetch_live_or_curated_papers("01_rl_tictactoe", stage="background", attempt_live_network=False)
    assert len(curated) >= 20


def test_dynamic_toc_subsection_injection_into_thesis_mock_expander(tmp_path: Path):
    """Verify that expand_academic_chapters dynamically injects subsection titles from academic_blueprint.json / TOC."""
    from adk.benchmarks import get_benchmark_task
    from adk.mocks.thesis_mock_expander import expand_academic_chapters
    from adk.tools.planning import synthesize_table_of_contents

    spec = get_benchmark_task("01_rl_tictactoe")
    ws = tmp_path / "ws_toc"
    ws.mkdir(parents=True, exist_ok=True)
    (ws / "core.py").write_text(spec.core_code, encoding="utf-8")

    toc = synthesize_table_of_contents(spec.task_id, thesis_type="inzynierska", title_pl=spec.title_pl)
    custom_sub_title = "Niestandardowa Sekcja Rekonesansu Planera 1.1"
    toc["chapters"][0]["subsections"][0]["title"] = custom_sub_title
    (ws / "academic_blueprint.json").write_text(
        json.dumps({"table_of_contents": toc}, ensure_ascii=False),
        encoding="utf-8",
    )

    expanded = expand_academic_chapters(
        spec=spec,
        base_chapters=spec.thesis_chapters,
        workspace_dir=ws,
        config_pairs=[("ALPHA", "0.15"), ("GAMMA", "0.95")],
        headers=["method", "win_rate", "draw_rate", "loss_rate"],
        rows=[
            {"method": "baseline", "win_rate": "0.42", "draw_rate": "0.12", "loss_rate": "0.46"},
            {"method": "proposed", "win_rate": "0.89", "draw_rate": "0.09", "loss_rate": "0.02"},
        ],
        is_ieee=False,
    )
    assert len(expanded) == 6
    assert custom_sub_title in expanded[0][1]
    assert "\\section{Niestandardowa Sekcja Rekonesansu Planera 1.1}" in expanded[0][1]


def test_vertical_feature_slices_in_single_task_planner():
    """Verify that task_planner cleanly produces vertical feature slices with co-evolving code, tests, and documentation, along with academic_blueprint."""
    planner_res = call_agent(
        "agents/planning/task_planner.md",
        {"user_prompt": "Build Q-learning agent with unit tests and thesis documentation"},
        model_tier="LRM",
        provider="mock",
    )
    assert planner_res["status"] == "ok"
    tasks = planner_res["output"]["tasks"]
    assert len(tasks) >= 2
    target_nodes = {t["target_node"] for t in tasks}
    assert "v1" in target_nodes or "v2" in target_nodes

    # Academic blueprint must be part of single task_planner output (not a separate thesis_architect)
    blueprint = planner_res["output"]["academic_blueprint"]
    assert "thesis_title" in blueprint
    assert "thesis_statement" in blueprint
    assert len(blueprint["planned_chapters"]) >= 4


def test_unknown_topic_gets_no_borrowed_methodology():
    from adk.tools.planning.research_recon import scout_domain_conventions

    recon = scout_domain_conventions("Kompresja modeli językowych metodą destylacji wiedzy", prescribe_methodology=True)
    assert recon["task_key"] == ""
    assert recon["standard_metrics"] == []
    assert recon["available_citation_keys"] == []


_ARXIV_ATOM = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2301.01234v2</id>
    <published>2023-01-03T00:00:00Z</published>
    <title>Tabular Q-Learning Revisited</title>
    <summary>We propose a method. However, it assumes small state spaces.</summary>
    <author><name>Ada Lovelace</name></author>
  </entry>
</feed>"""


class _FakeResponse:
    def __init__(self, body: bytes):
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False


def _fake_arxiv(monkeypatch, body: bytes | None):
    import adk.tools.building.literature_engine as engine

    engine._ARXIV_CACHE.clear()
    calls: list[str] = []

    def _urlopen(req, timeout=None):  # noqa: ARG001
        calls.append(req.full_url)
        if body is None:
            raise OSError("arXiv unreachable")
        return _FakeResponse(body)

    monkeypatch.setattr(engine.urllib.request, "urlopen", _urlopen)
    return calls


def test_live_recon_leaves_metrics_and_structure_to_the_plan(monkeypatch):
    from adk.tools.planning.research_recon import scout_domain_conventions

    calls = _fake_arxiv(monkeypatch, _ARXIV_ATOM)
    recon = scout_domain_conventions("tabular Q-Learning for Tic-Tac-Toe", prescribe_methodology=False)
    assert recon["standard_metrics"] == []
    assert recon["canonical_baselines"] == []
    assert recon["common_structural_patterns"] == []
    # Literature comes from arXiv only, with the arXiv identifier in every BibTeX entry.
    assert calls and all("export.arxiv.org" in url for url in calls)
    assert recon["citation_source"] == "arxiv"
    assert recon["available_citation_keys"] == ["lovelace2023tabular"]
    assert "eprint = {2301.01234}" in recon["verified_bibtex"]
    assert "archivePrefix = {arXiv}" in recon["verified_bibtex"]


def test_live_recon_without_arxiv_gets_no_substitute_literature(monkeypatch):
    from adk.tools.planning.research_recon import scout_domain_conventions

    _fake_arxiv(monkeypatch, None)
    recon = scout_domain_conventions("tabular Q-Learning for Tic-Tac-Toe", prescribe_methodology=False)
    assert recon["available_citation_keys"] == []
    assert recon["verified_bibtex"] == ""


def test_benchmark_prompts_dictate_no_files_values_or_metrics():
    from adk.benchmarks.tasks import BENCHMARK_TASKS

    dictated = ("config.py", "core.py", "results.csv", "train_and_evaluate", "ALPHA", "EPISODES", "win_rate", "\\ref_")
    for key, spec in BENCHMARK_TASKS.items():
        assert not [tok for tok in dictated if tok in spec.prompt], key
