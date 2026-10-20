from __future__ import annotations

import json
from pathlib import Path

from adk.core.llm import call_agent
from adk.tools.planning import calculate_blast_radius, select_model_tier


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
