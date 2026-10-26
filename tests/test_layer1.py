from __future__ import annotations

import json
from pathlib import Path

from adk.core.llm import _extract_json_from_text, call_agent
from adk.tools.planning import (
    calculate_blast_radius,
    escalate_node_weight,
    get_scoped_hypergraph_context,
    select_model_tier,
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


def test_blast_radius_and_complexity_router():
    matrix_path = Path(__file__).resolve().parent.parent / "adk" / "state" / "hypergraph_matrix.json"
    res = calculate_blast_radius("v1", matrix_path)
    assert res["degree"] >= 2
    assert "E1" in res["active_edges"]
    assert "v2" in res["affected_nodes"]

    assert select_model_tier("v1", matrix_path) == "LRM"
    assert select_model_tier("v4", matrix_path) == "LRM"


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


