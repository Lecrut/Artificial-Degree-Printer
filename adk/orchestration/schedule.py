"""The scheduler on the project hypergraph (Audit VI A7): tasks run when their vertex is ready, a failure blocks only
what depends on it, nothing planned is lost when the queue is rebuilt."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from adk.hypergraph import save
from adk.hypergraph.oracles import is_stub
from adk.hypergraph.schedule import CONTENT_STATE, readiness, vertex_of
from adk.orchestration.common import THESIS_FILE, _RunState

VERTEX_BUDGET = 8  # tasks (first build + repairs) on one vertex in one run, over all queue generations
_OPEN = ("TODO", "WAITING")


class SchedulerMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

    def _task_vertex(self, task: dict[str, Any]) -> str | None:
        h = self._project_h()
        if h is None:
            return None
        target = str(task.get("target_node", "")).replace("\\", "/")
        vertex = vertex_of(h, target, str(task.get("description", "")))
        # A helper file is worked on as part of the module that owns it.
        return vertex or h.owner_of(target)

    def _set_vertex_state(self, vertex: str, state: str, **why: Any) -> None:
        h = self._project_h()
        if h is None or vertex not in h.vertices or h.vertices[vertex].state == state:
            return
        h.vertices[vertex].state = state
        save(h, self.hypergraph_path)
        self.logger.log_event("VERTEX_STATE", vertex=vertex, state=state, **why)

    def _task_order(self, state: _RunState) -> Iterator[tuple[int, dict[str, Any]]]:
        """Next task to run, chosen after every task so readiness sees the latest states."""
        h = self._project_h()
        announced: set[str] = set()
        while True:
            planned = {v for t in state.tasks if t.get("status") in _OPEN and (v := self._task_vertex(t))}
            pick: tuple[int, dict[str, Any]] | None = None
            for idx, task in enumerate(state.tasks):
                if task.get("status") not in _OPEN:
                    continue
                vertex = self._task_vertex(task)
                if vertex and h is not None and h.vertices[vertex].attempts >= VERTEX_BUDGET:
                    task["status"] = "FAILED"
                    self.logger.log_event("VERTEX_BUDGET_SPENT", vertex=vertex, task_id=task.get("task_id"))
                    continue
                reasons = readiness(h, vertex, planned) if vertex and h is not None else []
                if reasons:
                    task["status"] = "WAITING"
                    if str(task.get("task_id")) not in announced:
                        announced.add(str(task.get("task_id")))
                        self.logger.log_event("TASK_WAITING", task_id=task.get("task_id"), vertex=vertex, reasons=reasons)
                    continue
                pick = (idx, task)
                break
            if pick is None:
                return
            idx, task = pick
            task["status"] = "TODO"
            vertex = self._task_vertex(task)
            if vertex and h is not None:
                h.vertices[vertex].attempts += 1
                save(h, self.hypergraph_path)
            yield idx, task

    def _on_task_result(self, task: dict[str, Any], passed: bool) -> None:
        """Vertex state after a task: verified when its verification passed, otherwise the content it now has."""
        vertex = self._task_vertex(task)
        if vertex is None:
            if str(task.get("target_node", "")).startswith(THESIS_FILE):
                self._chapter_states_from_thesis(passed, task)
            return
        kind = self._project_h().vertices[vertex].kind
        if passed:
            self._set_vertex_state(vertex, "verified", task_id=task.get("task_id"))
            return
        path = self.workspace_dir / vertex.partition("#")[0]
        if kind in ("code", "entry") and (not path.is_file() or is_stub(path.read_text(encoding="utf-8"))):
            return
        if kind not in ("code", "entry") and not path.is_file():
            return
        self._set_vertex_state(vertex, CONTENT_STATE.get(kind, "drafted"), task_id=task.get("task_id"))

    def _chapter_states_from_thesis(self, passed: bool, task: dict[str, Any]) -> None:
        """A thesis task that names no single chapter (several at once, a critic's fixes): every planned chapter
        now present in thesis.md takes the task's outcome (mock 01, 2026-11-18: six chapters written, all `spec`)."""
        from adk.orchestration.factual_audit import thesis_missing_chapters

        h = self._project_h()
        thesis = self.workspace_dir / THESIS_FILE
        if h is None or not thesis.is_file():
            return
        chapters = sorted(int(v.rpartition("#ch")[2]) for v in h.vertices if v.startswith(f"{THESIS_FILE}#ch"))
        titles = self._planned_chapter_titles()
        expected = {n: titles.get(n, "") for n in chapters}
        missing = set(thesis_missing_chapters(thesis.read_text(encoding="utf-8", errors="replace"), expected))
        for number in (n for n in chapters if n not in missing):
            self._set_vertex_state(f"{THESIS_FILE}#ch{number}", "verified" if passed else "drafted", task_id=task.get("task_id"))

    def _carry_over(self, tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Planned work a queue generation did not get to: it goes on into the next one (02, 2026-11-16: the
        rebuilt queues held only repairs, and the blocked implementation of the entrypoint never ran — X1)."""
        carried = [
            {**t, "status": "TODO"}
            for t in tasks
            if t.get("status") in _OPEN and "_FIX" not in str(t.get("task_id", ""))
        ]
        if carried:
            self.logger.log_event("TASKS_CARRIED", task_ids=[t.get("task_id") for t in carried])
        return carried
