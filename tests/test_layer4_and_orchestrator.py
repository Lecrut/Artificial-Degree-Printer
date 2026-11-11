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
from adk.tools.verification import run_isolated_tests
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
    assert "CONSOLIDATED_EPOCH" in redacted_text
    assert "## LEARNED RULES AND CONSTRAINTS" in redacted_text

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

    ws_dir = adk_dir / "workspace"
    (ws_dir / "bad_code.py").write_text("# FORBIDDEN token inside\nx = 1\n", encoding="utf-8")
    ver_fail = run_isolated_tests(ws_dir, use_docker=False, verification_dir=ver_dir)
    assert ver_fail["status"] == "FAIL"
    assert ver_fail["custom_validators_passed"] is False

    (ws_dir / "bad_code.py").write_text("x = 1\n", encoding="utf-8")
    ver_pass = run_isolated_tests(ws_dir, use_docker=False, verification_dir=ver_dir)
    assert ver_pass["status"] == "PASS"
    assert ver_pass["custom_validators_passed"] is True


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


def test_edge_scoped_verification_skips_symbolic_auditor_for_v1(tmp_path: Path):
    adk_dir = _clone_adk_env(tmp_path)
    orch = NeuroSymbolicOrchestrator(adk_root=adk_dir, enable_layer4=True, include_docs=True, provider="mock")

    # Prepare workspace where results.csv is older than config.py; editing v1 should NOT fail on stale_csv_files
    ws = adk_dir / "workspace"
    (ws / "config.py").write_text("ALPHA: float = 0.2\n", encoding="utf-8")
    (ws / "results.csv").write_text("method,win_rate\nbaseline,0.5\nproposed,0.8\n", encoding="utf-8")

    v1_task = {
        "task_id": "T1",
        "description": "Edit config.py parameters",
        "target_node": "v1",
        "assigned_agent": "seed_coder",
        "status": "IN_PROGRESS",
    }
    report_v1 = orch._run_verification_step(v1_task, include_docs=True, is_final_gate=False)
    assert report_v1["status"] == "PASS"
    assert report_v1["supervisors"]["symbolic_auditor"]["status"] == "SKIPPED_OUT_OF_EDGE_SCOPE"
    assert report_v1["supervisors"]["redteam_critic_guard"]["status"] == "SKIPPED_OUT_OF_EDGE_SCOPE"


def test_split_agent_updates_task_queue_assigned_agents(tmp_path: Path):
    adk_dir = _clone_adk_env(tmp_path)
    orch = NeuroSymbolicOrchestrator(adk_root=adk_dir, enable_layer4=True, include_docs=True, provider="mock")

    initial_queue = [
        {
            "task_id": "T2",
            "description": "Implement unit tests for core.py",
            "target_node": "v2",
            "assigned_agent": "seed_tester",
            "status": "FAILED",
        },
        {
            "task_id": "T2_EDGE",
            "description": "Verify edge case boundary conditions",
            "target_node": "v5",
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


def test_interactive_gates_callback_and_weight_escalation_in_orchestrator(tmp_path: Path):
    adk_dir = _clone_adk_env(tmp_path)

    # 1. Verify WEIGHT_ESCALATED is recorded when a task fails in Layer 3
    orch = NeuroSymbolicOrchestrator(adk_root=adk_dir, enable_layer4=True, include_docs=False, provider="mock")
    res = orch.run("Test EvoRoute weight escalation", simulate_first_attempt_fail=True)
    assert res["status"] == "COMPLETED"
    history = json.loads((adk_dir / "state" / "evolution_history.json").read_text(encoding="utf-8"))
    assert any(e["type"] == "WEIGHT_ESCALATED" for e in history["events"])
    matrix_after = json.loads((adk_dir / "state" / "hypergraph_matrix.json").read_text(encoding="utf-8"))
    assert matrix_after["nodes"]["v1"]["weight"] >= 1.4

    # 2. Verify gate_approval_callback can pause execution at GATE_2_METHODOLOGY_APPROVAL
    visited_gates: list[str] = []

    def _reject_gate2(gate_name: str, _ctx: dict) -> bool:
        visited_gates.append(gate_name)
        return gate_name != "GATE_2_METHODOLOGY_APPROVAL"

    res_paused = orch.run(
        "Test HITL gate rejection",
        simulate_first_attempt_fail=False,
        gate_approval_callback=_reject_gate2,
    )
    assert res_paused["status"] == "HITL_PAUSED"
    assert res_paused["gate"] == "GATE_2_METHODOLOGY_APPROVAL"
    assert "GATE_1_OUTLINE_APPROVAL" in visited_gates
    assert "GATE_2_METHODOLOGY_APPROVAL" in visited_gates


def test_orchestrator_resolve_target_node(tmp_path: Path):
    adk_dir = _clone_adk_env(tmp_path)
    orch = NeuroSymbolicOrchestrator(adk_root=adk_dir, provider="mock")

    # 1. Direct node ID hit
    nid, npath = orch._resolve_target_node("v2")
    assert nid == "v2"
    assert npath == "core.py"

    # 2. File path hit
    nid, npath = orch._resolve_target_node("core.py")
    assert nid == "v2"

    # 3. Unknown node with task context pointing to core.py
    task_hint = {"task_id": "T3_FIX", "description": "Fix winner logic in core.py"}
    nid, npath = orch._resolve_target_node("v7", task=task_hint)
    assert nid == "v2"
    assert npath == "core.py"

    # 4. Unknown node with no hints falls back safely to default
    nid, npath = orch._resolve_target_node("v99", fallback="v1")
    assert nid == "v1"




def test_collect_report_issues_reads_supervisor_issues():
    from adk.orchestrator import _collect_report_issues

    report = {
        "status": "FAIL",
        "supervisors": {
            "code_auditor": {"status": "FAIL", "issues": ["Pytest failure: AttributeError: module 'core' has no attribute 'x'"]},
            "symbolic_auditor": {"status": "SKIPPED_OUT_OF_EDGE_SCOPE", "issues": []},
            "redteam_critic_guard": {"status": "FAIL", "issues": ["Pytest failure: AttributeError: module 'core' has no attribute 'x'"]},
        },
        "issues": ["builder crashed"],
    }
    assert _collect_report_issues(report) == [
        "builder crashed",
        "Pytest failure: AttributeError: module 'core' has no attribute 'x'",
    ]
    assert _collect_report_issues({"status": "PASS"}) == []


def test_real_pytest_errors_come_first_in_code_audit(tmp_path: Path, monkeypatch):
    import adk.orchestrator as orch_mod

    real_call_agent = orch_mod.call_agent

    def fake_call_agent(agent_md, payload, *args, **kwargs):
        if "code_auditor" in str(agent_md):
            return {"output": {"status": "FAIL", "issues": ["LLM paraphrase of the failure"]}}
        return real_call_agent(agent_md, payload, *args, **kwargs)

    monkeypatch.setattr(orch_mod, "call_agent", fake_call_agent)
    adk_dir = _clone_adk_env(tmp_path)
    orch = NeuroSymbolicOrchestrator(adk_root=adk_dir, enable_layer4=True, include_docs=True, provider="mock")
    ws = adk_dir / "workspace"
    (ws / "core.py").write_text("def get_board():\n    return []\n", encoding="utf-8")
    (ws / "test_core.py").write_text(
        "import core\n\n\ndef test_missing():\n    assert core.is_terminal([])\n", encoding="utf-8"
    )
    task = {"task_id": "T5", "target_node": "v5", "assigned_agent": "seed_tester", "status": "IN_PROGRESS"}

    report = orch._run_verification_step(task, include_docs=True, is_final_gate=False)

    assert report["status"] == "FAIL"
    issues = report["supervisors"]["code_auditor"]["issues"]
    assert "is_terminal" in issues[0]
    assert "LLM paraphrase of the failure" in issues
    # The hyperedge contract (E4: core.py <-> test_core.py) names the exact violation.
    assert any("core.is_terminal" in v for v in report["contract_violations"])


def test_evolution_runs_once_per_distinct_failure(tmp_path: Path):
    adk_dir = _clone_adk_env(tmp_path)
    orch = NeuroSymbolicOrchestrator(adk_root=adk_dir, enable_layer4=True, include_docs=False, provider="mock")

    real_verify = orch._run_verification_step
    real_evolve = orch._run_evolution_step
    calls = {"verify": 0, "evolve": 0}

    def same_failure_three_times(task, *args, **kwargs):
        calls["verify"] += 1
        if calls["verify"] <= 3:
            return {
                "status": "FAIL",
                "failed_task_id": task.get("task_id"),
                "failed_node": "v1",
                "failed_file": "config.py",
                "failed_agent": "seed_coder",
                # Differing timings must not make it look like a new failure.
                "supervisors": {"code_auditor": {"status": "FAIL", "issues": [f"Pytest failure: 1 failed in 0.{calls['verify']}s"]}},
                "summary": "Layer 3 verification failed.",
            }
        return real_verify(task, *args, **kwargs)

    def counting_evolve(*args, **kwargs):
        calls["evolve"] += 1
        return real_evolve(*args, **kwargs)

    orch._run_verification_step = same_failure_three_times
    orch._run_evolution_step = counting_evolve

    res = orch.run("Zbuduj moduł walidacji parametrów")

    assert calls["evolve"] == 1
    actions = [c["w4_action"] for c in res.get("architecture_cycles", [])]
    # 3 failing verifications -> 3 retry iterations: W4 on the first, skipped on the two identical repeats.
    assert actions[:3] == ["MUTATE_AGENT", "SKIPPED_SAME_FAILURE", "SKIPPED_SAME_FAILURE"]
