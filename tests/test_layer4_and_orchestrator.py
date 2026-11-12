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
    assert max(meta["weight"] for meta in matrix_after["nodes"].values()) >= 1.4

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

    # 1. A legacy role alias resolves to the file playing the role; the node id is opaque.
    core_id, npath = orch._resolve_target_node("v2")
    assert npath == "core.py"
    assert not core_id.startswith("v")

    # 2. File path hit returns the same node
    nid, npath = orch._resolve_target_node("core.py")
    assert nid == core_id

    # 3. Unknown node with task context pointing to core.py
    task_hint = {"task_id": "T3_FIX", "description": "Fix winner logic in core.py"}
    nid, npath = orch._resolve_target_node("v7", task=task_hint)
    assert nid == core_id
    assert npath == "core.py"

    # 4. Unknown node with no hints falls back to the declared fallback role
    nid, npath = orch._resolve_target_node("v99", fallback="v1")
    assert npath == "config.py"

    # 5. A role is played by what the system created: a declared entrypoint becomes the core file.
    orch.blueprint_path.write_text(json.dumps({"entrypoint": "src/train.py:main"}), encoding="utf-8")
    _nid, npath = orch._resolve_target_node("v2")
    assert npath == "src/train.py"




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
    # W4 on the first failure, skipped on the first identical repeat; the second repeat means the prompt change
    # did not help, so the failure is reported as a suspected harness defect instead of burning more retries.
    assert actions[:3] == ["MUTATE_AGENT", "SKIPPED_SAME_FAILURE", "REPORT_HARNESS_BUG"]
    history = json.loads((adk_dir / "state" / "evolution_history.json").read_text(encoding="utf-8"))
    assert any(e.get("type") == "HARNESS_BUG_REPORTED" for e in history["events"])


def _grounding_fixture(tmp_path: Path) -> tuple[Path, Path]:
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "config.py").write_text("ALPHA = 0.1\nEPISODES: int = 10\n", encoding="utf-8")
    (ws / "core.py").write_text("import config\n\ndef train_and_evaluate():\n    return config.ALPHA\n", encoding="utf-8")
    (ws / "results.csv").write_text("method,metric,value\nproposed,win_rate,0.5\n", encoding="utf-8")
    (ws / "ablation.csv").write_text("method,metric,value\nbaseline,loss_rate,0.2\n", encoding="utf-8")
    matrix_file = tmp_path / "hypergraph_matrix.json"
    matrix_file.write_text(json.dumps({"nodes": {}, "edges": {}, "matrix": {}}), encoding="utf-8")
    from adk.tools.building import sync_hypergraph_matrix

    sync_hypergraph_matrix(ws, matrix_file)
    return ws, matrix_file


def test_grounded_state_exposes_real_ast_symbols(tmp_path: Path):
    from adk.orchestrator import build_grounded_symbols
    from adk.tools.building import extract_hyperedge_exports

    ws, matrix_file = _grounding_fixture(tmp_path)
    grounded = build_grounded_symbols(extract_hyperedge_exports("ALL", matrix_file, ws))
    assert "config.py:ALPHA" in grounded["available_ast_symbols"]
    assert "config.py:EPISODES" in grounded["available_ast_symbols"]
    assert "core.py:train_and_evaluate" in grounded["available_ast_symbols"]
    assert "config.py" not in grounded["available_ast_symbols"]


def test_grounded_state_exposes_real_csv_columns(tmp_path: Path):
    from adk.orchestrator import build_grounded_symbols
    from adk.tools.building import extract_hyperedge_exports

    ws, matrix_file = _grounding_fixture(tmp_path)
    grounded = build_grounded_symbols(extract_hyperedge_exports("ALL", matrix_file, ws))
    assert "results.csv:value" in grounded["available_csv_columns"]
    assert "columns" not in grounded["available_csv_columns"]
    assert "row_selectors" not in grounded["available_csv_columns"]


def test_grounded_state_covers_every_csv_in_graph(tmp_path: Path):
    from adk.orchestrator import build_grounded_symbols
    from adk.tools.building import extract_hyperedge_exports

    ws, matrix_file = _grounding_fixture(tmp_path)
    grounded = build_grounded_symbols(extract_hyperedge_exports("ALL", matrix_file, ws))
    assert "ablation.csv:value" in grounded["available_csv_columns"]


_RUFF_F841 = (
    "Ruff lint failure: F841 Local variable `{name}` is assigned to but never used\n"
    "  --> adk\\workspace\\benchmarks\\_evolved_adk_state\\workspace\\plot_results.py:{line}:9\n"
)


def test_issue_signature_ignores_renamed_identifiers_and_line_numbers():
    from adk.orchestrator import _issue_signature

    sigs = {
        _issue_signature({"issues": [_RUFF_F841.format(name=name, line=line)]})
        for name, line in (("width", 19), ("bars", 24), ("plot_df", 17))
    }
    assert sigs == {"plot_results.py:F841"}


def test_issue_signature_distinguishes_files_and_rules():
    from adk.orchestrator import _issue_signature

    a = _issue_signature({"issues": [_RUFF_F841.format(name="x", line=1)]})
    b = _issue_signature({"issues": [_RUFF_F841.format(name="x", line=1).replace("plot_results.py", "core.py")]})
    assert a != b


def test_rebuild_queue_detects_oscillating_failures(tmp_path: Path):
    adk_dir = _clone_adk_env(tmp_path)
    orch = NeuroSymbolicOrchestrator(adk_root=adk_dir, provider="mock")
    audits = iter(
        [
            {"pytest_status": "FAIL", "pytest_errors": [_RUFF_F841.format(name="width", line=19)]},
            {"pytest_status": "FAIL", "pytest_errors": ["FAILED test_core.py::test_draw - AssertionError"]},
            {"pytest_status": "FAIL", "pytest_errors": [_RUFF_F841.format(name="plot_df", line=17)]},
        ]
    )
    orch._audit_factual_state = lambda _report: next(audits)
    seen: list[str] = []
    assert "tasks" in orch._rebuild_queue({}, 0, seen)
    assert "tasks" in orch._rebuild_queue({}, 1, seen)
    # Third audit repeats the first one under another variable name: A -> B -> A is a repeat.
    assert "stop" in orch._rebuild_queue({}, 2, seen)


def test_mechanical_lint_is_fixed_by_tool_not_reported_as_failure(tmp_path: Path):
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "plot_results.py").write_text(
        "def plot(values):\n    width = 0.35\n    return sum(values)\n", encoding="utf-8"
    )
    res = run_isolated_tests(ws, verification_dir=tmp_path / "no_validators")
    assert res["ruff_passed"] is True
    assert not any("F841" in err for err in res["errors"])
    assert "width" not in (ws / "plot_results.py").read_text(encoding="utf-8")


def test_blocking_lint_still_fails_verification(tmp_path: Path):
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "core.py").write_text("def run():\n    return undefined_name + 1\n", encoding="utf-8")
    res = run_isolated_tests(ws, verification_dir=tmp_path / "no_validators")
    assert res["ruff_passed"] is False
    assert any("F821" in err for err in res["errors"])


def test_materialization_raises_when_agent_content_lands_nowhere(tmp_path: Path):
    import pytest

    from adk.orchestrator import MaterializationError

    adk_dir = _clone_adk_env(tmp_path)
    orch = NeuroSymbolicOrchestrator(adk_root=adk_dir, provider="mock")
    orch.provider = "ollama"  # the guard is disabled for the mock fallback path
    with pytest.raises(MaterializationError):
        orch._materialize_workspace_artifact("results.csv", {"source_code": "def plot():\n    return 1\n"})


def test_materialization_accepts_files_list_for_any_path(tmp_path: Path):
    adk_dir = _clone_adk_env(tmp_path)
    orch = NeuroSymbolicOrchestrator(adk_root=adk_dir, provider="mock")
    orch.provider = "ollama"
    orch._materialize_workspace_artifact(
        "results.csv", {"files": [{"filename": "plot_results.py", "content": "def plot():\n    return 1\n"}]}
    )
    assert (adk_dir / "workspace" / "plot_results.py").exists()


def _orch_with_workspace(tmp_path: Path, files: dict[str, str]) -> NeuroSymbolicOrchestrator:
    from adk.tools.building import sync_hypergraph_matrix

    adk_dir = _clone_adk_env(tmp_path)
    orch = NeuroSymbolicOrchestrator(adk_root=adk_dir, provider="mock")
    for rel, body in files.items():
        (orch.workspace_dir / rel).parent.mkdir(parents=True, exist_ok=True)
        (orch.workspace_dir / rel).write_text(body, encoding="utf-8")
    sync_hypergraph_matrix(orch.workspace_dir, orch.matrix_path)
    return orch


def test_audit_routes_lint_error_to_the_file_that_failed(tmp_path: Path):
    orch = _orch_with_workspace(tmp_path, {"plot_results.py": "X = 1\n", "core.py": "Y = 1\n"})
    ws = str(orch.workspace_dir).replace("/", "\\")
    err = (
        "Ruff lint failure: F841 Local variable `plot_df` is assigned to but never used\n"
        f"  --> {ws}\\plot_results.py:17:9\n"
    )
    tasks = orch._tasks_from_audit({"pytest_status": "FAIL", "pytest_errors": [err]}, 1)
    assert [t["target_node"] for t in tasks] == ["plot_results.py"]
    node_id, node_path = orch._resolve_target_node(tasks[0]["target_node"], task=tasks[0])
    assert node_path == "plot_results.py"


def test_audit_redirects_derived_artifact_to_its_producer(tmp_path: Path):
    orch = _orch_with_workspace(
        tmp_path,
        {
            "core.py": "def run():\n    import csv\n    open('results.csv', 'w').write('a')\n",
            "results.csv": "method,metric,value\n",
        },
    )
    tasks = orch._tasks_from_audit(
        {"pytest_status": "FAIL", "pytest_errors": ['File "results.csv", line 1\n  bad', "FAILED results.py"]}, 1
    )
    targets = {t["target_node"] for t in tasks}
    assert "results.csv" not in targets


def test_unknown_file_target_becomes_a_new_node_not_config(tmp_path: Path):
    orch = _orch_with_workspace(tmp_path, {})
    node_id, node_path = orch._resolve_target_node("src/models/dqn.py")
    assert node_path == "src/models/dqn.py"
    nodes = json.loads(orch.matrix_path.read_text(encoding="utf-8"))["nodes"]
    assert nodes[node_id]["path"] == "src/models/dqn.py"


def test_exhausted_budget_delivers_work_with_listed_gaps(tmp_path: Path):
    orch = _orch_with_workspace(tmp_path, {"thesis.md": "## Rozdział 1: Wstęp\n\nTekst.\n"})
    orch._audit_factual_state = lambda _report: {
        "pytest_status": "FAIL",
        "pytest_errors": ["FAILED test_core.py::test_draw - AssertionError"],
        "chapters_missing": [6],
        "trigger_issues": ["Wskaźnik remisów 12,6% opisano jako wysoki."],
    }
    res = orch._rebuild_queue({"status": "FAIL"}, 4, [])
    stop = res["stop"]
    assert stop["status"] == "COMPLETED_WITH_GAPS"
    kinds = {g["kind"] for g in stop["gaps"]}
    assert {"kod", "rozdział", "ustalenie weryfikacji"} <= kinds

    thesis = (orch.workspace_dir / "thesis.md").read_text(encoding="utf-8")
    assert "Braki i ograniczenia realizacji" in thesis
    assert "Brak rozdziału 6" in thesis
    report = json.loads(orch.validation_report_path.read_text(encoding="utf-8"))
    assert len(report["gaps"]) == len(stop["gaps"])
    hitl = json.loads(orch.hitl_flag_path.read_text(encoding="utf-8")) if orch.hitl_flag_path.exists() else {}
    assert hitl.get("current_gate") != "GATE_QUEUE_REBUILD_EXHAUSTED"


def test_critic_findings_become_tasks_with_ids(tmp_path: Path):
    orch = _orch_with_workspace(tmp_path, {"plot_results.py": "X = 1\n", "thesis.md": "## A\n"})
    tasks = orch._tasks_from_audit(
        {
            "pytest_status": "PASS",
            "csv_columns": ["method", "metric", "value"],
            "trigger_issues": [
                "W pliku plot_results.py warunek if 'unstack' jest zawsze prawdziwy.",
                "Rozdział 6 twierdzi, że nie było powtórzeń, a kod robi 50.",
                "Brak liczb w zdaniach o wynikach.",
            ],
        },
        2,
    )
    by_target = {t["target_node"]: t for t in tasks}
    assert "plot_results.py" in by_target
    critic = next(t for t in tasks if t["task_id"].endswith("_CRITIC"))
    assert "[K1]" in critic["description"] and "[K2]" in critic["description"]
    assert critic["assigned_agent"] == "seed_writer"


def test_findings_are_fitted_whole_with_a_count_note():
    from adk.orchestrator import _fit_items

    items = ["a" * 50, "b" * 50, "c" * 50]
    shown = _fit_items(items, max_chars=110)
    assert shown[:2] == items[:2]
    assert shown[-1].startswith("[pokazano 2 z 3")


def _evolution_with_decision(tmp_path: Path, decision: dict) -> tuple[NeuroSymbolicOrchestrator, dict]:
    from adk.core.llm import set_llm_handler

    adk_dir = _clone_adk_env(tmp_path)
    orch = NeuroSymbolicOrchestrator(adk_root=adk_dir, provider="mock")
    set_llm_handler(lambda *_args: decision)
    try:
        res = orch._run_evolution_step({"failed_agent": "seed_coder", "validation_report": {}})
    finally:
        set_llm_handler(None)
    return orch, res


def test_rule_naming_one_incident_is_not_written_into_the_prompt(tmp_path: Path):
    orch, res = _evolution_with_decision(
        tmp_path, {"action": "MUTATE_AGENT", "agent_id": "seed_coder", "rule": "Unikaj niezgodności w zadaniu T1 na węźle v1."}
    )
    assert res["action"] == "MUTATION_SKIPPED"
    coder = (orch.agents_dir / "building" / "seed_coder.md").read_text(encoding="utf-8")
    assert "zadaniu T1" not in coder


def test_missing_rule_does_not_inject_a_filler(tmp_path: Path):
    _orch, res = _evolution_with_decision(tmp_path, {"action": "MUTATE_AGENT", "agent_id": "seed_coder"})
    assert res["action"] == "MUTATION_SKIPPED"


def test_unusable_install_decision_is_not_laundered_into_a_mutation(tmp_path: Path):
    _orch, res = _evolution_with_decision(tmp_path, {"action": "INSTALL_DEPENDENCY"})
    assert res["action"] == "INSTALL_DEPENDENCY_SKIPPED"


def test_unknown_evolution_action_is_reported(tmp_path: Path):
    _orch, res = _evolution_with_decision(tmp_path, {"action": "REWRITE_EVERYTHING"})
    assert res["action"] == "UNKNOWN"


def test_install_package_skips_importable_module():
    from adk.tools.evolution.dependency_manager import install_package

    assert install_package("json")["status"] == "skipped"


def test_role_alias_never_collides_with_a_discovered_node(tmp_path: Path):
    """With an empty seed, discovered files get opaque ids. The legacy alias v4 must still mean the thesis,
    even when the graph already holds four or more nodes."""
    orch = _orch_with_workspace(
        tmp_path,
        {
            "config.py": "A = 1\n",
            "core.py": "import config\n",
            "plot_results.py": "X = 1\n",
            "thesis.compiled.md": "## A\n",
            "thesis.md": "## A\n",
        },
    )
    nodes = json.loads(orch.matrix_path.read_text(encoding="utf-8"))["nodes"]
    assert len(nodes) >= 5
    assert not any(node_id.startswith("v") for node_id in nodes)
    _nid, path = orch._resolve_target_node("v4")
    assert path == "thesis.md"


def test_role_is_played_by_the_file_the_system_created(tmp_path: Path):
    orch = _orch_with_workspace(tmp_path, {"settings.py": "SEED = 1\n", "test_agent.py": "def test_x():\n    pass\n"})
    assert orch._role_file("config") == "settings.py"
    assert orch._role_file("tests") == "test_agent.py"
    assert orch._role_file("core") == "core.py"  # nothing plays it yet: the default name


def test_unverified_bibtex_from_a_model_is_dropped(tmp_path: Path):
    adk_dir = _clone_adk_env(tmp_path)
    orch = NeuroSymbolicOrchestrator(adk_root=adk_dir, provider="mock")
    orch.provider = "ollama"
    orch.blueprint_path.write_text(
        json.dumps({"literature_recon": {"citation_source": "arxiv", "available_citation_keys": ["real2023paper"]}}),
        encoding="utf-8",
    )
    bib = (
        "@article{real2023paper,\n  title = {Real},\n  year = {2023}\n}\n\n"
        "@article{invented2024paper,\n  title = {Hallucinated},\n  year = {2024}\n}"
    )
    orch._materialize_workspace_artifact("references.bib", {"bibtex_entries": bib})
    written = (adk_dir / "workspace" / "references.bib").read_text(encoding="utf-8")
    assert "real2023paper" in written
    assert "invented2024paper" not in written


def test_declared_metrics_are_compared_with_what_was_measured(tmp_path: Path):
    from adk.orchestrator import _declared_vs_measured_metrics

    (tmp_path / "results.csv").write_text(
        "method,metric,value\nproposed,win_rate,0.6\nproposed,episode_length,7\n", encoding="utf-8"
    )
    findings = _declared_vs_measured_metrics(["win_rate", "draw_rate"], tmp_path)
    assert any("'draw_rate'" in f and "nie została zmierzona" in f for f in findings)
    assert any("'episode_length'" in f and "nie była zadeklarowana" in f for f in findings)
    assert not any("'win_rate'" in f for f in findings)
    # Before the experiment has run there is nothing to compare yet.
    assert _declared_vs_measured_metrics(["win_rate"], tmp_path / "empty") == []
