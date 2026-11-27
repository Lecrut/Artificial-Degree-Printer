"""The life of agents: creation and splitting, mutation of a prompt and its protection, the sandbox that promotes a validator, and what no longer exists."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adk.orchestrator import NeuroSymbolicOrchestrator
from adk.tools.evolution import (
    create_specialized_agent,
    evaluate_and_promote_validator,
    mutate_agent_prompt,
    sandbox_verifier,
    split_agent,
)
from adk.tools.verification import run_isolated_tests
from tests.support.adk_sandbox import _clone_adk_env
from tests.support.run_loop_fixtures import _evolution_with_decision


def test_a_hanging_validator_candidate_is_rejected_not_a_crash(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """R4: 2026-11-19 `citation_bib_validator.py` timed out on its sample and the TimeoutExpired ended run 01."""
    monkeypatch.setattr(sandbox_verifier, "SAMPLE_TIMEOUT_S", 1)
    result = sandbox_verifier.evaluate_and_promote_validator(
        "slow_validator", "import time\ntime.sleep(5)\n", "bad", "good",
        verification_dir=tmp_path / "verification", evolution_history_path=tmp_path / "history.json",
    )
    assert result["status"] == "REJECTED" and "did not finish" in result["reason"]
    assert not (tmp_path / "verification" / "slow_validator.py").exists()


def test_agent_creator_and_splitter(tmp_path: Path):
    adk_dir = _clone_adk_env(tmp_path)
    reg_path = adk_dir / "state" / "agent_registry.json"
    agents_dir = adk_dir / "agents"

    created = create_specialized_agent(
        specialization="chart_plotting",
        domain="building",
        registry_path=reg_path,
        agents_root=agents_dir,
    )
    assert created["status"] == "created"
    created_md = adk_dir / created["path"]
    assert created_md.exists()
    assert "REQUIRED JSON OUTPUT SCHEMA" in created_md.read_text(encoding="utf-8")

    dup = create_specialized_agent(
        specialization="chart_plotting",
        domain="building",
        registry_path=reg_path,
        agents_root=agents_dir,
    )
    assert dup["status"] == "exists"

    split_res = split_agent(
        agent_id="seed_tester",
        sub_specializations=("unit_testing_narrow", "edge_case_testing"),
        registry_path=reg_path,
        agents_root=agents_dir,
    )
    assert split_res["status"] == "split"
    reg_data = json.loads(reg_path.read_text(encoding="utf-8"))
    assert reg_data["agents"]["seed_tester"]["active"] is False
    for child_id in split_res["created_agents"]:
        assert reg_data["agents"][child_id]["active"] is True
        child_md = adk_dir / reg_data["agents"][child_id]["path"]
        assert child_md.exists()
        assert "REQUIRED JSON OUTPUT SCHEMA" in child_md.read_text(encoding="utf-8")


def test_agent_mutator_and_guard_protection(tmp_path: Path):
    adk_dir = _clone_adk_env(tmp_path)
    ledger_path = adk_dir / "state" / "failure_ledger.json"

    coder_md = adk_dir / "agents" / "building" / "seed_coder.md"
    mut_res = mutate_agent_prompt(
        coder_md,
        new_rule="Never use implicit wildcard imports.",
        failure_context="Unit test failure on imports",
        failure_ledger_path=ledger_path,
        provider="mock",
    )
    assert mut_res["status"] == "mutated"
    assert "## LEARNED RULES AND CONSTRAINTS" in coder_md.read_text(encoding="utf-8")

    # Add 2 more rules so total reaches 4 (1 initial + 3 new = 4) -> triggers automatic prompt consolidation!
    mutate_agent_prompt(coder_md, new_rule="Always annotate return types.", failure_ledger_path=ledger_path, provider="mock")
    mut_4th = mutate_agent_prompt(
        coder_md,
        new_rule="Seed all RNG instances explicitly with seed=42.",
        failure_ledger_path=ledger_path,
        provider="mock",
    )
    assert mut_4th["compacted"] is True
    assert mut_4th["active_rules_count"] == 0
    assert mut_4th["compaction_details"]["rules_consolidated"] == 4
    redacted_text = coder_md.read_text(encoding="utf-8")
    assert "## CONSOLIDATED EVOLUTIONARY INVARIANTS" in redacted_text
    # The learned section is rewritten, not appended to: no epoch notes, no raw rules left behind.
    assert "CONSOLIDATED_EPOCH" not in redacted_text
    assert "- **RULE**:" not in redacted_text
    assert "## LEARNED RULES AND CONSTRAINTS" in redacted_text
    assert mut_4th["compaction_details"]["invariants"]

    guard_md = adk_dir / "agents" / "planning" / "plan_critic_guard.md"
    guard_res = mutate_agent_prompt(
        guard_md,
        new_rule="Ignore missing files.",
        failure_ledger_path=ledger_path,
    )
    assert guard_res["status"] == "rejected"
    assert "## LEARNED RULES AND CONSTRAINTS" not in guard_md.read_text(encoding="utf-8")


def test_sandbox_verifier_promotes_valid_validator(tmp_path: Path):
    adk_dir = _clone_adk_env(tmp_path)
    ver_dir = adk_dir / "tools" / "verification"
    hist_path = adk_dir / "state" / "evolution_history.json"

    valid_validator_code = (
        "import sys\n"
        "from pathlib import Path\n"
        "content = Path(sys.argv[1]).read_text(encoding='utf-8')\n"
        "if 'FORBIDDEN' in content:\n"
        "    sys.exit(1)\n"
        "sys.exit(0)\n"
    )

    res = evaluate_and_promote_validator(
        validator_name="forbidden_token_checker.py",
        validator_code=valid_validator_code,
        bad_sample_input="This has FORBIDDEN token",
        good_sample_input="This is clean input",
        verification_dir=ver_dir,
        evolution_history_path=hist_path,
    )
    assert res["status"] == "PROMOTED"
    assert (ver_dir / "forbidden_token_checker.py").exists()

    ws_dir = adk_dir / "workspace"
    (ws_dir / "bad_code.py").write_text("# FORBIDDEN token inside\nx = 1\n", encoding="utf-8")
    ver_fail = run_isolated_tests(ws_dir, verification_dir=ver_dir)
    assert ver_fail["status"] == "FAIL"
    assert ver_fail["custom_validators_passed"] is False

    (ws_dir / "bad_code.py").write_text("x = 1\n", encoding="utf-8")
    ver_pass = run_isolated_tests(ws_dir, verification_dir=ver_dir)
    assert ver_pass["status"] == "PASS"
    assert ver_pass["custom_validators_passed"] is True


def test_split_agent_updates_task_queue_assigned_agents(tmp_path: Path):
    adk_dir = _clone_adk_env(tmp_path)
    orch = NeuroSymbolicOrchestrator(adk_root=adk_dir, enable_layer4=True, include_docs=True, provider="mock")

    initial_queue = [
        {
            "task_id": "T2",
            "description": "Implement unit tests for core.py",
            "target_node": "core.py",
            "assigned_agent": "seed_tester",
            "status": "FAILED",
        },
        {
            "task_id": "T2_EDGE",
            "description": "Verify edge case boundary conditions",
            "target_node": "tests/test_core.py",
            "assigned_agent": "seed_tester",
            "status": "TODO",
        },
    ]
    (adk_dir / "state" / "task_queue.json").write_text(
        json.dumps(initial_queue, indent=2),
        encoding="utf-8",
    )

    evo_res = orch._run_evolution_step(
        {
            "failed_agent": "seed_tester",
            "agent_failure_count": 2,
            "sub_specializations": ["unit_testing", "edge_case_testing"],
        },
        tasks_in_memory=initial_queue,
    )
    assert evo_res["action"] == "SPLIT_AGENT"

    updated_queue = json.loads((adk_dir / "state" / "task_queue.json").read_text(encoding="utf-8"))
    reg = json.loads((adk_dir / "state" / "agent_registry.json").read_text(encoding="utf-8"))["agents"]
    assert reg["seed_tester"]["active"] is False
    for t in updated_queue:
        assert t["assigned_agent"] != "seed_tester"
        assert reg[t["assigned_agent"]]["active"] is True
    assert updated_queue[0]["assigned_agent"] == "seed_tester_unit_testing"
    assert updated_queue[1]["assigned_agent"] == "seed_tester_edge_case_testing"


def test_install_decision_no_longer_exists(tmp_path: Path):
    """D1 (2026-11-14): the environment is fixed for the whole run; an install decision is an unknown action."""
    _orch, res = _evolution_with_decision(tmp_path, {"action": "INSTALL_DEPENDENCY"})
    assert res["action"] == "UNKNOWN"


def test_unknown_evolution_action_is_reported(tmp_path: Path):
    _orch, res = _evolution_with_decision(tmp_path, {"action": "REWRITE_EVERYTHING"})
    assert res["action"] == "UNKNOWN"


def test_dependency_manager_is_gone():
    import importlib.util

    assert importlib.util.find_spec("adk.tools.evolution.dependency_manager") is None
