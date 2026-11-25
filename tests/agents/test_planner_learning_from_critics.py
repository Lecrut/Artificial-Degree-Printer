"""Blocking findings of the planning critics are failures of the planner that wrote the part; a pattern (two different places) evolves that planner's prompt once per run."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from adk.orchestration.plan_evolution import CRITIC_CATEGORY
from adk.orchestrator import NeuroSymbolicOrchestrator

RULE = "When you give an example in an interface, work out its value by hand before you write it, because the example is checked later against real code."


def _orch(tmp_path: Path, layer4: bool = True) -> tuple[NeuroSymbolicOrchestrator, list[dict[str, Any]]]:
    root = tmp_path / "adk"
    (root / "agents" / "planning").mkdir(parents=True)
    (root / "agents" / "evolution").mkdir(parents=True)
    (root / "state").mkdir()
    (root / "agents" / "planning" / "plan_module.md").write_text("# plan_module\n", encoding="utf-8")
    (root / "agents" / "evolution" / "evolution_architect.md").write_text("# architect\n", encoding="utf-8")
    (root / "state" / "agent_registry.json").write_text(json.dumps({"agents": {}}), encoding="utf-8")
    orch = NeuroSymbolicOrchestrator(adk_root=str(root), enable_layer4=layer4, provider="mock")
    asked: list[dict[str, Any]] = []

    def fake(_md: Any, payload: dict, **_kw: Any) -> dict:
        asked.append(payload)
        return {"status": "ok", "output": {"decision": "MUTATE_AGENT", "agent_id": "plan_module", "rule": RULE}}

    orch._call_agent = fake
    return orch, asked


def test_one_blocked_place_is_not_a_pattern(tmp_path: Path) -> None:
    orch, asked = _orch(tmp_path)
    orch._learn_from_critic("plan_module", "src/a.py", ["PLAN_CRITIC [src/a.py]: x"])
    orch._learn_from_critic("plan_module", "src/a.py", ["PLAN_CRITIC [src/a.py]: y"])  # the same module again
    assert asked == []


def test_planner_keeps_learning_on_new_evidence_only(tmp_path: Path) -> None:
    orch, asked = _orch(tmp_path)
    orch._learn_from_critic("plan_module", "src/a.py", ["PLAN_CRITIC [src/a.py]: first"])
    orch._learn_from_critic("plan_module", "src/b.py", ["PLAN_CRITIC [src/b.py]: second"])
    orch._learn_from_critic("plan_module", "src/c.py", ["PLAN_CRITIC [src/c.py]: third"])
    assert len(asked) == 1  # one new place after the rule is not a pattern
    orch._learn_from_critic("plan_module", "src/d.py", ["PLAN_CRITIC [src/d.py]: fourth"])
    assert len(asked) == 2 and asked[1]["pattern"]["tasks"] == ["src/c.py", "src/d.py"]
    orch._learn_from_critic("plan_module", "src/e.py", ["PLAN_CRITIC [src/e.py]: fifth"])
    assert len(asked) == 2  # again a single new place
    pattern = asked[0]["pattern"]
    assert pattern["category"] == CRITIC_CATEGORY and pattern["tasks"] == ["src/a.py", "src/b.py"]
    assert asked[0]["failed_agent"] == "plan_module"
    assert RULE in (orch.agents_dir / "planning" / "plan_module.md").read_text(encoding="utf-8")
    log = json.loads(orch.failure_ledger_path.read_text(encoding="utf-8"))["category_log"]
    assert [e["agent"] for e in log] == ["plan_module"] * 5 and {e["category"] for e in log} == {CRITIC_CATEGORY}
    rules = json.loads(orch.failure_ledger_path.read_text(encoding="utf-8"))["rules"]
    assert rules[0]["category"] == CRITIC_CATEGORY and rules[0]["cycle"] == 2


def test_each_planner_is_counted_separately(tmp_path: Path) -> None:
    orch, asked = _orch(tmp_path)
    orch._learn_from_critic("plan_module", "src/a.py", ["f"])
    orch._learn_from_critic("plan_outline", "outline:2", ["g"])
    assert asked == []


def test_layer4_off_logs_but_does_not_evolve(tmp_path: Path) -> None:
    orch, asked = _orch(tmp_path, layer4=False)
    orch._learn_from_critic("plan_module", "src/a.py", ["f"])
    orch._learn_from_critic("plan_module", "src/b.py", ["g"])
    assert asked == [] and len(orch._critic_log) == 2


def test_the_simulated_architect_writes_a_rule_for_the_planner_instead_of_splitting_it(tmp_path: Path) -> None:
    from adk.mocks.agents import SimulatedAgents
    from adk.mocks.scenarios import SCENARIOS

    orch, _asked = _orch(tmp_path)
    simulated = SimulatedAgents(SCENARIOS["default"])
    orch._call_agent = lambda md, payload, **_k: {"status": "ok", "output": simulated(Path(md).stem, "", payload, "LRM")}
    orch._learn_from_critic("plan_module", "src/a.py", ["PLAN_CRITIC [src/a.py]: first"])
    orch._learn_from_critic("plan_module", "src/b.py", ["PLAN_CRITIC [src/b.py]: second"])
    learned = (orch.agents_dir / "planning" / "plan_module.md").read_text(encoding="utf-8")
    assert "state what every value means" in learned
