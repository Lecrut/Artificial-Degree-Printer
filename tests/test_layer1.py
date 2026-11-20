from __future__ import annotations

import json
from pathlib import Path

from adk.core.llm import _extract_json_from_text, call_agent
from adk.tools.planning import (
    scout_domain_conventions,
    select_model_tier,
)


def test_state_files_initialized():
    root = Path(__file__).resolve().parent.parent / "adk" / "state"
    expected = [
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


def test_complexity_router_follows_the_attempt():
    # The tier follows the attempt, not the node: the small model works, the large one steps in after two failures.
    assert select_model_tier() == "SML"
    assert select_model_tier(failures=1) == "SML"
    assert select_model_tier(failures=2) == "LRM"


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
        "agents/planning/plan_critic_guard.md",
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


def test_scout_domain_conventions_routes_research_and_prescribes_nothing():
    """Reconnaissance routes the research by degree and takes its literature from the installed paper source (here
    the simulated catalog); it never prescribes the project (§XIII F3) and builds no table of contents (F4)."""
    recon_rl = scout_domain_conventions("01_rl_tictactoe", thesis_type="inzynierska")
    assert recon_rl["research_routing"] == ["background_researcher"]
    assert recon_rl["citation_source"] == "catalog"
    assert len(recon_rl["available_citation_keys"]) >= 10
    assert not any(key in recon_rl for key in ("task_key", "domain", "algorithm_focus", "standard_metrics", "canonical_baselines", "common_structural_patterns"))
    assert "@" in recon_rl["verified_bibtex"]

    recon_anom = scout_domain_conventions("02_ml_anomaly_detection", thesis_type="magisterska")
    assert recon_anom["research_routing"] == ["background_researcher", "discoverer_researcher"]

    recon_fl = scout_domain_conventions("04_federated_learning", thesis_type="paper")
    assert recon_fl["research_routing"] == ["discoverer_researcher"]


def test_research_first_task_ordering_in_planner():
    """The simulated planner of every benchmark plans the research first and the chapters last."""
    from adk.benchmarks import BENCHMARK_TASKS
    from adk.mocks.agents import SimulatedAgents
    from adk.mocks.scenarios import SCENARIOS

    for task_id, spec in BENCHMARK_TASKS.items():
        agents = SimulatedAgents(SCENARIOS[task_id])
        plan_out = agents("task_planner", "", {"user_prompt": spec.prompt, "error_feedback": "none"}, "LRM")
        tasks = plan_out["tasks"]
        assert plan_out["academic_blueprint"]["planned_chapters"], task_id
        assert tasks[0]["target_node"] == "thesis.md" and "researcher" in tasks[0]["assigned_agent"], task_id
        assert tasks[-1]["target_node"] == "thesis.md" and tasks[-1]["assigned_agent"] == "seed_writer", task_id


def test_paper_card_extraction_and_arxiv_parser():
    """Verify dynamic PaperCard extraction from abstracts and from arXiv Atom XML."""
    from adk.tools.building.literature_engine import (
        _parse_arxiv_atom_xml,
        extract_paper_card_from_abstract,
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
    assert f"@article{{{card['key']}," in format_bibtex(card)

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
    assert {"config.py", "core.py"} <= target_nodes
    # Every plan carries the specification its tasks build on (Audit VI).
    assert set(planner_res["output"]["interfaces"]) == {"config.py", "core.py", "plot_results.py"}  # figures: §XIII.8

    # Academic blueprint must be part of single task_planner output (not a separate thesis_architect)
    blueprint = planner_res["output"]["academic_blueprint"]
    assert "thesis_title" in blueprint
    assert "thesis_statement" in blueprint
    assert len(blueprint["planned_chapters"]) >= 4


def test_unknown_topic_gets_no_borrowed_methodology(monkeypatch):
    from adk.tools.building.literature_engine import set_paper_source
    from adk.tools.planning.research_recon import scout_domain_conventions

    set_paper_source(None)
    _fake_arxiv(monkeypatch, None)
    recon = scout_domain_conventions("Kompresja modeli językowych metodą destylacji wiedzy")
    assert not any(key in recon for key in ("task_key", "domain", "algorithm_focus", "standard_metrics", "canonical_baselines", "common_structural_patterns"))
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

    from adk.tools.building.literature_engine import set_paper_source

    set_paper_source(None)  # the harness's own source: arXiv
    calls = _fake_arxiv(monkeypatch, _ARXIV_ATOM)
    recon = scout_domain_conventions("tabular Q-Learning for Tic-Tac-Toe")
    assert not any(key in recon for key in ("task_key", "domain", "algorithm_focus", "standard_metrics", "canonical_baselines", "common_structural_patterns"))
    # Literature comes from arXiv only, with the arXiv identifier in every BibTeX entry.
    assert calls and all("export.arxiv.org" in url for url in calls)
    assert recon["citation_source"] == "arxiv"
    assert recon["available_citation_keys"] == ["lovelace2023tabular"]
    assert "eprint = {2301.01234}" in recon["verified_bibtex"]
    assert "archivePrefix = {arXiv}" in recon["verified_bibtex"]


def test_live_recon_without_arxiv_gets_no_substitute_literature(monkeypatch):
    from adk.tools.planning.research_recon import scout_domain_conventions

    from adk.tools.building.literature_engine import set_paper_source

    set_paper_source(None)
    _fake_arxiv(monkeypatch, None)
    recon = scout_domain_conventions("tabular Q-Learning for Tic-Tac-Toe")
    assert recon["available_citation_keys"] == []
    assert recon["verified_bibtex"] == ""


def test_benchmark_prompts_dictate_no_files_values_or_metrics():
    from adk.benchmarks.tasks import BENCHMARK_TASKS

    dictated = ("config.py", "core.py", "results.csv", "train_and_evaluate", "ALPHA", "EPISODES", "win_rate", "\\ref_")
    for key, spec in BENCHMARK_TASKS.items():
        assert not [tok for tok in dictated if tok in spec.prompt], key
