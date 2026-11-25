"""Story: a module fails after every repair, the queue ends, the designer revises the design, the module is designed and built again and the run completes with what worked kept."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from adk.orchestration.common import _RunState
from adk.orchestrator import NeuroSymbolicOrchestrator


def _events_of(orch: NeuroSymbolicOrchestrator, since: int, *kinds: str) -> list[dict]:
    lines = orch.logger.events_path.read_text(encoding="utf-8").splitlines()[since:]
    return [e for e in map(json.loads, lines) if e["event"] in kinds]


def test_a_whole_run_redesigns_after_a_failed_module_and_completes(tmp_path: Path) -> None:
    """The real loop of `run`: the first task on `core.py` ends as if its repairs were spent, the queue goes on and
    ends, the designer is asked, the failed module is designed and built again, and the run completes."""
    from adk.mocks import install_simulated_agents
    from tests.support.adk_sandbox import _clone_adk_env

    install_simulated_agents(flaws=set())
    orch = NeuroSymbolicOrchestrator(adk_root=_clone_adk_env(tmp_path), enable_layer4=False, provider="mock")
    execute, failed_once = orch._execute_task, []

    def spend_the_repairs(state: _RunState, idx: int, task: dict[str, Any]) -> dict[str, Any] | None:
        if not failed_once and Path(str(task["target_node"])).name == "core.py":
            failed_once.append(task["task_id"])
            task["status"] = "FAILED"
            orch._mark_failed({"failed_file": "core.py"}, task)
            return None
        return execute(state, idx, task)

    orch._execute_task = spend_the_repairs
    seen = len(orch.logger.events_path.read_text(encoding="utf-8").splitlines()) if orch.logger.events_path.exists() else 0  # the log is shared
    result = orch.run("Zbuduj moduł walidacji parametrów")
    assert failed_once and result["status"] == "COMPLETED"
    assert [e["event"] for e in _events_of(orch, seen, "REDESIGN_STARTED", "REDESIGN_GUIDELINES", "REDESIGN_APPLIED")] == [
        "REDESIGN_STARTED", "REDESIGN_GUIDELINES", "REDESIGN_APPLIED",
    ]
    applied = _events_of(orch, seen, "REDESIGN_APPLIED")[-1]
    assert applied["redesigned"] == ["core.py"] and "config.py" in applied["kept"]
    h = orch._project_h()
    assert h.vertices["core.py"].state == "verified" and h.vertices["config.py"].state == "verified"
    assert any(t["task_id"].startswith("D1_") and t["status"] == "DONE" for t in result["tasks"])
