"""Tests for blocker vs warning gradation, critic proof checks, progress budgets, and partial patch acceptance."""

from __future__ import annotations

from pathlib import Path

from adk.orchestrator import NeuroSymbolicOrchestrator


def _make_orch(tmp_path: Path) -> NeuroSymbolicOrchestrator:
    orch = NeuroSymbolicOrchestrator(adk_root="adk", enable_layer4=False, provider="mock")
    orch.workspace_dir = tmp_path / "workspace"
    orch.state_dir = tmp_path / "state"
    orch.workspace_dir.mkdir(parents=True, exist_ok=True)
    orch.state_dir.mkdir(parents=True, exist_ok=True)
    orch.task_queue_path = orch.state_dir / "task_queue.json"
    orch.validation_report_path = orch.state_dir / "validation_report.json"
    orch.blueprint_path = orch.state_dir / "academic_blueprint.json"
    orch.failure_ledger_path = orch.state_dir / "failure_ledger.json"
    orch.hitl_flag_path = orch.state_dir / "hitl_flag.json"
    orch.evolution_history_path = orch.state_dir / "evolution_history.json"
    return orch


_MOD_A = 'def helper_a() -> int:\n    """Return 1."""\n    return 1\n'
_MOD_B = 'def helper_b() -> int:\n    """Return 2."""\n    return 2\n'
_EXP = (
    "from src.mod_a import helper_a\n"
    "from src.mod_b import helper_b\n\n"
    'def run_experiment() -> int:\n    """Run."""\n    return helper_a() + helper_b()\n'
)
_ENTRY = "src/experiment.py:run_experiment"


def _base_plan() -> dict:
    return {
        "tasks": [
            {"task_id": "T1", "target_node": "src/mod_a.py", "description": "Implement helper_a"},
            {"task_id": "T2", "target_node": "src/mod_b.py", "description": "Implement helper_b"},
            {"task_id": "T3", "target_node": "src/experiment.py", "description": "Implement run_experiment"},
        ],
        "interfaces": {
            "src/mod_a.py": _MOD_A,
            "src/mod_b.py": _MOD_B,
            "src/experiment.py": _EXP,
        },
        "entrypoint": _ENTRY,
        "academic_blueprint": {"thesis_statement": "A+B=3", "entrypoint": _ENTRY},
    }


def test_unproven_critic_blocker_is_downgraded_to_warning_and_passes(tmp_path: Path):
    orch = _make_orch(tmp_path)
    planner_calls = []

    def agents(md, payload, **_kw):
        if Path(md).name == "plan_critic_guard.md":
            return {
                "status": "ok",
                "output": {
                    "status": "FAIL",
                    "issues": [
                        # Missing real target in plan -> downgraded to warning
                        {"blocking": True, "where": "nonexistent_module.py", "problem": "vague", "fix": "do something"},
                        # Missing fix -> downgraded to warning
                        {"blocking": True, "where": "src/mod_a.py", "problem": "missing edge test", "fix": ""},
                        # Explicit warning
                        {"blocking": False, "where": "src/mod_b.py", "problem": "style", "fix": "rename"},
                    ],
                },
            }
        planner_calls.append(payload)
        return {"status": "ok", "output": {}}

    orch._call_agent = agents
    _, _, blockers = orch._validated_plan(_base_plan(), {"user_prompt": "p"}, tmp_path / "planner.md")
    assert blockers == []
    assert planner_calls == []


def test_gaps_are_blocking_until_fixed(tmp_path: Path):
    orch = _make_orch(tmp_path)
    plan = _base_plan()
    plan["tasks"][0]["description"] = "Call undeclared_symbol() in helper_a"
    planner_calls = []

    def agents(md, payload, **_kw):
        if Path(md).name == "plan_critic_guard.md":
            return {"status": "ok", "output": {"status": "PASS", "issues": []}}
        planner_calls.append(payload)
        fixed_tasks = [dict(t) for t in plan["tasks"]]
        fixed_tasks[0]["description"] = "Implement helper_a"
        return {"status": "ok", "output": {"tasks": fixed_tasks}}

    orch._call_agent = agents
    out_plan, _, blockers = orch._validated_plan(plan, {"user_prompt": "p"}, tmp_path / "planner.md")
    assert blockers == []
    assert len(planner_calls) == 1
    assert "BLOCKERS" in planner_calls[0]["error_feedback"]
    assert out_plan["tasks"][0]["description"] == "Implement helper_a"


def test_progress_budget_allows_more_than_two_patches_and_separates_code_vs_critic(tmp_path: Path):
    orch = _make_orch(tmp_path)
    plan = _base_plan()
    plan["interfaces"]["src/mod_a.py"] = _MOD_A.replace("int", "Optional[int]")  # missing Optional import
    critic_step = 0
    planner_step = 0

    def agents(md, _payload, **_kw):
        nonlocal critic_step, planner_step
        if Path(md).name == "plan_critic_guard.md":
            critic_step += 1
            if critic_step == 1:
                return {
                    "status": "ok",
                    "output": {
                        "status": "FAIL",
                        "issues": [
                            {"blocking": True, "where": "academic_blueprint.thesis_statement", "problem": "too vague", "fix": "specify metric"}
                        ],
                    },
                }
            if critic_step == 2:
                return {
                    "status": "ok",
                    "output": {
                        "status": "FAIL",
                        "issues": [
                            {"blocking": True, "where": "src/mod_b.py", "problem": "returns 2 instead of 3", "fix": "update docstring"}
                        ],
                    },
                }
            return {"status": "ok", "output": {"status": "PASS", "issues": []}}

        planner_step += 1
        if planner_step == 1:
            return {"status": "ok", "output": {"interfaces": {"src/mod_a.py": _MOD_A}}}
        if planner_step == 2:
            return {"status": "ok", "output": {"academic_blueprint": {"thesis_statement": "A+B=3 measured by sum"}}}
        return {"status": "ok", "output": {"interfaces": {"src/mod_b.py": _MOD_B.replace("Return 2.", "Return 2 (baseline).")}}}

    orch._call_agent = agents
    _, _, blockers = orch._validated_plan(plan, {"user_prompt": "p"}, tmp_path / "planner.md")
    assert blockers == []
    assert planner_step == 3
    assert critic_step == 3


def test_partial_patch_keeps_valid_module_and_rejects_broken_module(tmp_path: Path):
    orch = _make_orch(tmp_path)
    plan = _base_plan()
    plan["interfaces"]["src/mod_a.py"] = _MOD_A.replace("int", "Optional[int]")  # missing Optional import
    planner_step = 0

    def agents(md, _payload, **_kw):
        nonlocal planner_step
        if Path(md).name == "plan_critic_guard.md":
            return {"status": "ok", "output": {"status": "PASS", "issues": []}}
        planner_step += 1
        if planner_step == 1:
            # Fixes mod_a.py, but breaks mod_b.py with an undefined name
            return {
                "status": "ok",
                "output": {
                    "interfaces": {
                        "src/mod_a.py": _MOD_A,
                        "src/mod_b.py": "def helper_b() -> UnknownType:\n    return 2\n",
                    }
                },
            }
        # On the second attempt, current_plan already has the fixed mod_a.py, so nothing left to fix if no other error;
        # wait: mod_b.py stayed as _MOD_B, so code_blockers is already empty after partial patch!
        return {"status": "ok", "output": {}}

    orch._call_agent = agents
    out_plan, _, blockers = orch._validated_plan(plan, {"user_prompt": "p"}, tmp_path / "planner.md")
    assert blockers == []
    assert out_plan["interfaces"]["src/mod_a.py"] == _MOD_A
    assert out_plan["interfaces"]["src/mod_b.py"] == _MOD_B
    assert planner_step == 1


def test_growing_critic_blockers_stops_after_no_progress_limit(tmp_path: Path):
    orch = _make_orch(tmp_path)
    plan = _base_plan()
    critic_step = 0
    planner_step = 0

    def agents(md, _payload, **_kw):
        nonlocal critic_step, planner_step
        if Path(md).name == "plan_critic_guard.md":
            critic_step += 1
            # Critic keeps inflating blockers: 1 -> 2 -> 3
            issues = [
                {"blocking": True, "where": "src/mod_a.py", "problem": f"issue {i}", "fix": f"fix {i}"}
                for i in range(critic_step)
            ]
            return {"status": "ok", "output": {"status": "FAIL", "issues": issues}}
        planner_step += 1
        return {
            "status": "ok",
            "output": {"academic_blueprint": {"thesis_statement": f"updated {planner_step}"}},
        }

    orch._call_agent = agents
    _, _, blockers = orch._validated_plan(plan, {"user_prompt": "p"}, tmp_path / "planner.md")
    assert len(blockers) == 3
    assert planner_step == 2


def test_task_dict_patch_updates_only_targeted_task_preserving_count(tmp_path: Path):
    orch = _make_orch(tmp_path)
    plan = _base_plan()
    plan["tasks"][0]["description"] = "Call undeclared_symbol() in helper_a"

    def agents(md, _payload, **_kw):
        if Path(md).name == "plan_critic_guard.md":
            return {"status": "ok", "output": {"status": "PASS", "issues": []}}
        return {"status": "ok", "output": {"tasks": {"T1": {"description": "Implement helper_a"}}}}

    orch._call_agent = agents
    out_plan, _, blockers = orch._validated_plan(plan, {"user_prompt": "p"}, tmp_path / "planner.md")
    assert blockers == []
    assert len(out_plan["tasks"]) == 3
    assert out_plan["tasks"][0]["description"] == "Implement helper_a"
    assert out_plan["tasks"][1:] == plan["tasks"][1:]


