"""Re-plan of what failed (Audit §XI A). A task that used up its repairs marks the vertex it failed on as `failed`;
what depends on it waits (readiness), everything independent goes on. When nothing is left to run, the planner
gets the dossier of the failed part — what works, what failed, every attempt and why it was refused — together with
the current plan, and writes new tasks for that part (it may also change a failed module's interface, validated
like the plan). The harness orders them through readiness on H.

2026-11-18: after qagent.py failed, its tests and the experiment ran on it anyway and were repaired for its fault;
the queue rebuilt from the audit sent the same tasks to the same agent four times without anyone asking why."""

from __future__ import annotations

from typing import Any

from adk.core.models import read_json_state, write_json_state
from adk.hypergraph import Hypergraph, save
from adk.hypergraph.schedule import FAILED, readiness
from adk.orchestration import agent_texts as texts
from adk.orchestration.common import _RunState, _agent_for_path
from adk.orchestration.plan_interfaces import _plan_interfaces
from adk.orchestration.plan_spec import _plan_view

REPLANS_WITHOUT_PROGRESS = 2  # re-plans in a row after which no new vertex was verified: the run ends with gaps
MAX_REPLANS = 6
_REPLANNABLE = ("code", "entry", "test", "chapter")


def _dependents(h: Hypergraph, vertex: str) -> list[str]:
    """What waits for `vertex`: the users and tests of a module, the experiment it is part of and its outputs,
    the chapters citing it."""
    found: set[str] = set()
    for edge in h.edges.values():
        role = edge.members.get(vertex)
        if role == "P" or (role == "C" and edge.type != "I"):
            found |= set(edge.members) - {vertex}
    return sorted(found)


class FragmentReplanMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

    def _failed_vertices(self) -> list[str]:
        h = self._project_h()
        return sorted(v for v, x in h.vertices.items() if x.state == FAILED) if h is not None else []

    def _mark_failed(self, report: dict[str, Any], task: dict[str, Any]) -> str | None:
        """The vertex a task finally failed on: the one the verdict blames (its file's owner), else the task's."""
        h = self._project_h()
        if h is None:
            return None
        blamed = h.owner_of(str(report.get("failed_file") or "")) or self._task_vertex(task)
        if blamed not in h.vertices or h.vertices[blamed].kind not in _REPLANNABLE:
            return None
        self._set_vertex_state(blamed, FAILED, task_id=task.get("task_id"))
        return blamed

    def _waits_on_failed(self, task: dict[str, Any]) -> bool:
        """Whether the task's vertex now has to wait (readiness on H), e.g. a test whose module just failed."""
        h = self._project_h()
        vertex = self._task_vertex(task)
        return h is not None and vertex is not None and bool(readiness(h, vertex, set()))

    def _code_vertex_of(self, report: dict[str, Any]) -> str | None:
        """The code or test vertex a failed verdict blames, if it blames one."""
        h = self._project_h()
        owner = h.owner_of(str(report.get("failed_file") or "")) if h is not None else None
        return owner if owner is not None and h.vertices[owner].kind in ("code", "entry", "test") else None

    def _repair_dossier(self, h: Hypergraph, failed: list[str]) -> dict[str, Any]:
        blueprint = read_json_state(self.blueprint_path) if self.blueprint_path.exists() else {}
        interfaces = blueprint.get("interfaces") or {}
        entries = []
        for vertex in failed:
            v = h.vertices[vertex]
            path = self.workspace_dir / vertex.partition("#")[0]
            module = h.tested_module(vertex) if v.kind == "test" else vertex
            entries.append({
                "vertex": vertex,
                "kind": v.kind,
                "planned_interface": interfaces.get(module, "") if module else "",
                "current_content": path.read_text(encoding="utf-8", errors="replace")[:6000] if path.is_file() and v.kind != "chapter" else "",
                "attempts": v.attempts,
                "failures": v.failures,
                "history": v.history,
                "last_writer": v.last_writer,
                "waiting_on_it": _dependents(h, vertex),
            })
        return {
            "failed": entries,
            "verified_do_not_touch": sorted(v for v, x in h.vertices.items() if x.state == "verified"),
            "entrypoint": blueprint.get("entrypoint"),
        }

    def _replan_failed(self, state: _RunState) -> dict[str, Any] | None:
        """None when nothing failed; {"tasks": [...]} after a re-plan; {"stop": payload} when re-planning is spent."""
        failed = self._failed_vertices()
        if not failed:
            return None
        h = self._project_h()
        progress = self.__dict__.setdefault("_replan_progress", [])
        progress.append(sum(1 for x in h.vertices.values() if x.state == "verified"))
        stalled = len(progress) > REPLANS_WITHOUT_PROGRESS and progress[-1] <= progress[-1 - REPLANS_WITHOUT_PROGRESS]
        if stalled or len(progress) > MAX_REPLANS:
            return {"stop": self._replan_exhausted(state, failed)}

        blueprint = read_json_state(self.blueprint_path) if self.blueprint_path.exists() else {}
        interfaces = _plan_interfaces(blueprint)
        dossier = self._repair_dossier(h, failed)
        print(f"\n  [PRZEPLANOWANIE {len(progress)}] Nieudane wierzchołki: {', '.join(failed)}", flush=True)
        self.logger.log_step("REPLAN", f"Przeplanowanie nieudanych wierzchołków ({len(failed)})", {"failed": failed})
        answer = self._call_agent(
            self.agents_dir / "planning" / "task_planner.md",
            {
                "user_prompt": self.current_user_prompt,
                "current_plan": _plan_view({"tasks": state.tasks, "academic_blueprint": blueprint}, interfaces),
                "repair_dossier": dossier,
                "error_feedback": texts.replan_failed_instruction(failed),
            },
            model_tier="LRM",
            provider=self.provider,
        )
        out = answer.get("output") if answer.get("status") == "ok" else None
        out = out if isinstance(out, dict) else {}
        changed = self._replan_interfaces(h, out, failed, interfaces, blueprint)
        tasks, dropped = self._replan_tasks(h, out, len(progress), state)
        self.logger.log_event(
            "REPLANNED", round=len(progress), failed=failed, tasks=[t["task_id"] for t in tasks],
            interfaces_changed=changed, dropped=dropped, gaps=out.get("gaps") or [],
        )
        state.tasks.extend(tasks)
        write_json_state(self.task_queue_path, state.tasks)
        print(f"  [PRZEPLANOWANIE {len(progress)}] {len(tasks)} nowych zadań; zmienione interfejsy: {changed or '-'}", flush=True)
        return {"tasks": tasks}

    def _replan_interfaces(
        self, h: Hypergraph, out: dict[str, Any], failed: list[str], interfaces: dict[str, str], blueprint: dict[str, Any]
    ) -> list[str]:
        """Interface changes of failed modules, each validated like the plan (`_apply_amendment`)."""
        allowed = {h.tested_module(v) if h.vertices[v].kind == "test" else v for v in failed}
        changed: list[str] = []
        for rel, source in _plan_interfaces(out).items():
            if rel not in allowed or interfaces.get(rel) == source or f"I:{rel}" not in h.edges:
                continue
            users = {
                e.id.removeprefix("I:"): e.spec.get("uses", {}).get(rel, [])
                for e in h.edges.values()
                if e.type == "I" and rel in e.spec.get("uses", {})
            }
            refused = self._apply_amendment(rel, source, interfaces, blueprint, users)
            if refused:
                self.logger.log_event("SPEC_AMEND_REJECTED", module=rel, task_id="REPLAN", violations=refused)
                continue
            interfaces[rel] = source
            h.vertices[rel].history.append({"task_id": "REPLAN", "issues": [f"Interface of {rel} changed by the re-plan."]})
            save(h, self.hypergraph_path)
            self.logger.log_event("SPEC_AMENDED", module=rel, rule="REPLAN", task_id="REPLAN", reason="re-plan of a failed module")
            changed.append(rel)
        return changed

    def _replan_tasks(
        self, h: Hypergraph, out: dict[str, Any], round_no: int, state: _RunState
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """New tasks of the re-plan: on vertices that are not verified, one per vertex that has no open task."""
        open_vertices = {self._task_vertex(t) for t in state.tasks if t.get("status") in ("TODO", "WAITING")}
        tasks: list[dict[str, Any]] = []
        dropped: list[str] = []
        for i, raw in enumerate(out.get("tasks") or [], 1):
            if not isinstance(raw, dict) or not raw.get("target_node"):
                dropped.append(str(raw)[:120])
                continue
            task = {
                "task_id": f"R{round_no}_{i}",
                "description": str(raw.get("description") or ""),
                "target_node": str(raw["target_node"]),
                "assigned_agent": str(raw.get("assigned_agent") or ""),
                "status": "TODO",
            }
            vertex = self._task_vertex(task)
            if vertex is None or h.vertices[vertex].state == "verified" or vertex in open_vertices:
                dropped.append(f"{task['target_node']}: {'verified' if vertex else 'not in the plan'} or already queued")
                continue
            task["assigned_agent"] = self._resolve_active_agent(task["assigned_agent"], fallback=_agent_for_path(vertex.partition("#")[0]))
            open_vertices.add(vertex)
            tasks.append(task)
        return tasks, dropped

    def _replan_exhausted(self, state: _RunState, failed: list[str]) -> dict[str, Any]:
        """The run ends with the failed part listed as gaps, like an exhausted queue."""
        self._shout_problem_stop(texts.replan_exhausted(failed))
        report = read_json_state(self.validation_report_path) if self.validation_report_path.exists() else {}
        audit = self._audit_factual_state(report)
        closing = self._finalize_with_gaps(audit, report)
        stop = {
            "status": "COMPLETED_WITH_GAPS",
            "reason": "REPLAN_EXHAUSTED",
            "failed_vertices": failed,
            "audit": audit,
            "gaps": closing["gaps"],
            "pdf_ok": closing["pdf_ok"],
        }
        stop.update(state.outcome(validation_report={**report, "gaps": closing["gaps"]}))
        return stop


