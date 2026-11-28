"""Resuming a run from restored state (`adk.benchmarks.resume`): the plan, the hypergraph and the files are there, so
planning is skipped and the queue continues where it stopped. What is verified stays verified; nothing is built twice."""

from __future__ import annotations

from typing import Any

from adk.core.models import read_json_state, write_json_state
from adk.hypergraph import save

# A task that was running or waiting for its turn goes on; a finished one is finished only while its vertex still is.
_REDO = ("IN_PROGRESS", "TODO")
_SETTLED_VERTEX = ("verified", "failed")


class ResumeMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

    def _resume_phase(self) -> dict[str, Any]:
        """Instead of `_plan_phase`: {"tasks": queue} to continue, or {"stop": payload} when there is no state to continue."""
        h = self._project_h()
        queue = read_json_state(self.task_queue_path) if self.task_queue_path.exists() else []
        tasks = [t for t in queue if isinstance(t, dict)]
        if h is None or not tasks:
            return {"stop": {"status": "RESUME_FAILED", "reason": "NO_STATE_TO_RESUME", "tasks": tasks, "replan_count": 0}}
        blueprint = read_json_state(self.blueprint_path) if self.blueprint_path.exists() else {}
        self.planned_thesis_type = str(blueprint.get("thesis_type") or "inzynierska")
        self.planned_template = str(blueprint.get("template_name") or "thesis_plodz")

        reopened: list[str] = []
        for task in tasks:
            vertex = self._task_vertex(task)
            if task.get("status") in _REDO:
                task["status"] = "TODO"
            elif task.get("status") == "DONE" and vertex and h.vertices[vertex].state not in _SETTLED_VERTEX:
                task["status"] = "TODO"  # done, but its vertex went stale or never got past the stub
                reopened.append(str(task.get("task_id")))
            if task["status"] == "TODO":
                task["repair_attempts"] = 0
        # A fresh budget for what is not verified: the run that stopped may have spent it.
        for vertex in h.vertices.values():
            if vertex.state != "verified":
                vertex.attempts = 0
        save(h, self.hypergraph_path)
        write_json_state(self.task_queue_path, tasks)

        verified = sorted(v.id for v in h.vertices.values() if v.state == "verified")
        counts: dict[str, int] = {}
        for task in tasks:
            counts[str(task.get("status"))] = counts.get(str(task.get("status")), 0) + 1
        self.logger.log_event("RUN_RESUMED", verified=verified, tasks=counts, reopened=reopened)
        print(
            f"\n[WZNOWIENIE] Zweryfikowane (pomijane): {len(verified)} wierzchołków {verified}; zadania: {counts}.",
            flush=True,
        )
        return {"tasks": tasks}
