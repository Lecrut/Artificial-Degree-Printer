"""An orchestrator prepared for the phases of a run (planning payload, verification of an intermediate and of the final task) and the planning agents that answer it."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from adk.orchestrator import NeuroSymbolicOrchestrator


def _setup_test_orchestrator(tmp_path: Path) -> NeuroSymbolicOrchestrator:
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
    # Without this every test run appended events to the tracked adk/state/evolution_history.json (§V pkt 21).
    orch.evolution_history_path = orch.state_dir / "evolution_history.json"
    return orch


def _staged_agents(plan: dict[str, Any], captured: list[tuple[str, dict]] | None = None, outline_answers: list[Any] | None = None):
    """call_agent answering `plan` stage by stage (§XVI); other agents get an empty answer."""
    from adk.mocks.staged import staged_answer

    def call(agent_md: Any, payload: dict[str, Any], **_kwargs: Any) -> dict[str, Any]:
        agent = Path(str(agent_md)).stem
        if captured is not None:
            captured.append((agent, payload))
        if agent == "plan_outline" and outline_answers:
            return {"status": "ok", "output": outline_answers.pop(0)}
        return {"status": "ok", "output": staged_answer(plan, agent, payload) or {}}

    return call
