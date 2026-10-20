from __future__ import annotations

import json
import shutil
from pathlib import Path

from adk.core.connection import LLMConnectionManager
from adk.orchestrator import NeuroSymbolicOrchestrator
from adk.tools.evolution import (
    create_specialized_agent,
    evaluate_and_promote_validator,
    mutate_agent_prompt,
    split_agent,
)
from main import run_scenario


def _clone_adk_env(tmp_path: Path) -> Path:
    src_adk = Path(__file__).resolve().parent.parent / "adk"
    dst_adk = tmp_path / "adk"
    shutil.copytree(src_adk / "state", dst_adk / "state")
    shutil.copytree(src_adk / "agents", dst_adk / "agents")
    shutil.copytree(src_adk / "tools", dst_adk / "tools")
    (dst_adk / "workspace").mkdir(parents=True, exist_ok=True)
    return dst_adk


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
    assert (adk_dir / created["path"]).exists()

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
        assert (adk_dir / reg_data["agents"][child_id]["path"]).exists()


def test_agent_mutator_and_guard_protection(tmp_path: Path):
    adk_dir = _clone_adk_env(tmp_path)
    ledger_path = adk_dir / "state" / "failure_ledger.json"

    coder_md = adk_dir / "agents" / "building" / "seed_coder.md"
    mut_res = mutate_agent_prompt(
        coder_md,
        new_rule="Never use implicit wildcard imports.",
        failure_context="Unit test failure on imports",
        failure_ledger_path=ledger_path,
    )
    assert mut_res["status"] == "mutated"
    assert "## LEARNED RULES AND CONSTRAINTS" in coder_md.read_text(encoding="utf-8")

    guard_md = adk_dir / "agents" / "planning" / "task_critic_guard.md"
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
        use_docker=False,
    )
    assert res["status"] == "PROMOTED"
    assert (ver_dir / "forbidden_token_checker.py").exists()


def test_orchestrator_wave1_and_wave2_loops(tmp_path: Path):
    adk_dir = _clone_adk_env(tmp_path)

    orch_w1 = NeuroSymbolicOrchestrator(adk_root=adk_dir, enable_layer4=False, provider="mock")
    res_w1 = orch_w1.run("Zbuduj moduł walidacji parametrów", simulate_first_attempt_fail=True)
    assert res_w1["status"] == "COMPLETED"
    assert res_w1["replan_count"] == 1
    assert all(t["status"] == "DONE" for t in res_w1["tasks"])

    orch_w2 = NeuroSymbolicOrchestrator(adk_root=adk_dir, enable_layer4=True, provider="mock")
    res_w2 = orch_w2.run(
        "Rozbuduj moduł o wykresy i raport",
        simulate_first_attempt_fail=True,
        missing_agent_specialization="latex_table_formatter",
    )
    assert res_w2["status"] == "COMPLETED"
    history = json.loads((adk_dir / "state" / "evolution_history.json").read_text(encoding="utf-8"))
    event_types = [e["type"] for e in history["events"]]
    assert "AGENT_CREATED" in event_types
    assert "AGENT_MUTATED" in event_types

    res_hitl = orch_w2.run("Sprzeczne wymagania", contradictory_requirements=True)
    assert res_hitl["status"] == "HITL_PAUSED"
    hitl_data = json.loads((adk_dir / "state" / "hitl_flag.json").read_text(encoding="utf-8"))
    assert hitl_data["active"] is True


def test_three_main_scenarios_and_logging(tmp_path: Path):
    adk_dir = _clone_adk_env(tmp_path)

    conn = LLMConnectionManager(provider="google")
    assert conn.resolve_provider() == "google"
    assert "gemini" in conn.resolve_model_name("google", "LRM")

    r1 = run_scenario("1", provider="mock", adk_root=adk_dir)
    assert r1["status"] == "COMPLETED"
    assert r1["mode"]["enable_layer4"] is False
    assert r1["mode"]["include_docs"] is False
    assert len(r1["tasks"]) == 2

    r2 = run_scenario("2", provider="mock", adk_root=adk_dir)
    assert r2["status"] == "COMPLETED"
    assert r2["mode"]["enable_layer4"] is True
    assert r2["mode"]["include_docs"] is False
    assert len(r2["tasks"]) == 2

    r3 = run_scenario("3", provider="mock", adk_root=adk_dir)
    assert r3["status"] == "COMPLETED"
    assert r3["mode"]["enable_layer4"] is True
    assert r3["mode"]["include_docs"] is True
    assert len(r3["tasks"]) == 3
    assert Path(r3["log_files"]["process_log"]).exists()
    assert Path(r3["log_files"]["agent_trace_jsonl"]).exists()
