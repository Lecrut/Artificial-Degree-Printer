"""Re-plan of what failed (Audit §XI A). A task that used up its repairs marks the vertex it failed on as `failed`;
what depends on it waits (readiness), everything independent goes on. When nothing is left to run, the planner
gets the dossier of the failed part — what works, what failed, every attempt and why it was refused — together with
the current plan, and writes new tasks for that part (it may also change a failed module's interface, validated
like the plan). The harness orders them through readiness on H.

2026-11-18: after qagent.py failed, its tests and the experiment ran on it anyway and were repaired for its fault;
the queue rebuilt from the audit sent the same tasks to the same agent four times without anyone asking why."""

from __future__ import annotations

import re
from typing import Any

from adk.core.models import read_json_state, write_json_state
from adk.hypergraph import Hypergraph, save
from adk.hypergraph.schedule import FAILED, readiness
from adk.orchestration import agent_texts as texts
from adk.orchestration.common import _RunState, _agent_for_path, available_package_imports
from adk.orchestration.failure_kinds import error_signature
from adk.orchestration.interface_view import interface_view
from adk.orchestration.plan_interfaces import _plan_interfaces

REPLANS_WITHOUT_PROGRESS = 3 # re-plans in a row after which no new vertex was verified: the run ends with gaps
MAX_REPLANS = 6
DEPENDENCY_CHARS = 20000  # code of one dependency in the dossier: whole modules (2026-11-23, 01: environment.py was cut at 4000 of 6165 characters, `step()` never reached the planner)
LATEST_ERROR_CHARS = 1500  # one finding of the current blocker copied into the task description
_REPLANNABLE = ("code", "entry", "test", "chapter")
_MARKERS = ("PLAN", "REPLAN")  # history entries written by the planner, not by a verification


def _latest_errors(history: list[dict[str, Any]]) -> list[str]:
    """What blocks the vertex now: the findings of the last verification, apart from the whole history (2026-11-23,
    01: in round 5 the planner answered the errors of round 2 and not the two missing metrics of the last attempt)."""
    for entry in reversed(history):
        if entry.get("task_id") not in _MARKERS and entry.get("issues"):
            return [str(i) for i in entry["issues"]]
    return []


def _history_before_latest(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The verdicts of a vertex without the one `_latest_errors` already gives: the same error was sent three times
    (`latest_errors`, the end of `history`, the task that carried it: §XXXVIII.2)."""
    for i in range(len(history) - 1, -1, -1):
        if history[i].get("task_id") not in _MARKERS and history[i].get("issues"):
            return history[:i] + history[i + 1:]
    return history


def _mentioned(text: str, rel: str) -> bool:
    """Whether a file is named in error text (a traceback frame `trainer.py:63`, a pytest path `tests\\test_x.py`)."""
    return re.search(rf"(?<!\w){re.escape(rel)}", text.replace("\\", "/")) is not None


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

    def _dependency_sources(self, h: Hypergraph, vertex: str, read: Any) -> dict[str, dict[str, str]]:
        """The modules a failed module uses (their state and code): the fault may be there, behind a `verified`
        (2026-11-22, 02: `generate_dataset` returned `None`, `experiment.py` was rewritten five times)."""
        edge = h.edges.get(f"I:{vertex}")
        if h.vertices[vertex].kind not in ("code", "entry") or edge is None:
            return {}
        used = [m for m in edge.spec.get("uses", {}) if m in h.vertices and h.vertices[m].kind in ("code", "entry")]
        return {m: {"state": h.vertices[m].state, "source": read(m)[:DEPENDENCY_CHARS]} for m in sorted(used)}

    def _dependent_sources(self, h: Hypergraph, vertex: str, read: Any, counterpart: set[str]) -> dict[str, dict[str, str]]:
        """The neighbours above a failed vertex (what uses it, what waits for it) that its own errors name: the
        caller may be the one at fault (2026-11-23, 01: `trainer.py` passed a board in a form `agent_qlearn.py` could
        not hash; the agent was rewritten five times). Together with `_dependency_sources` this is one rule: any
        neighbour named in the errors of a failed vertex is a suspect, whichever way the edge points."""
        text = " ".join(str(i) for e in h.vertices[vertex].history for i in e.get("issues", []))
        found = [
            d for d in _dependents(h, vertex)
            if d not in counterpart and d in h.vertices and h.vertices[d].kind in ("code", "entry", "test")
            and h.vertices[d].state != FAILED and _mentioned(text, d)
        ]
        return {d: {"state": h.vertices[d].state, "source": read(d)[:DEPENDENCY_CHARS]} for d in found}

    def _reopenable(self, h: Hypergraph, dossier: dict[str, Any]) -> set[str]:
        """Verified vertices a re-plan may reopen: what a failed module uses, what uses it or waits for it and its
        errors name, and the module a failed test checks."""
        found = {
            m for e in dossier["failed"] for key in ("dependencies", "dependents")
            for m, d in e.get(key, {}).items() if d["state"] == "verified"
        }
        for e in dossier["failed"]:
            module = h.tested_module(e["vertex"]) if e["kind"] == "test" else None
            if module in h.vertices and h.vertices[module].state == "verified" and h.vertices[module].kind in ("code", "entry"):
                found.add(module)
        return found - self.__dict__.setdefault("_replan_reopened", set())

    def _repair_dossier(self, h: Hypergraph, failed: list[str]) -> dict[str, Any]:
        blueprint = read_json_state(self.blueprint_path) if self.blueprint_path.exists() else {}
        interfaces = blueprint.get("interfaces") or {}
        entries = []
        def _read(rel: str) -> str:
            p = self.workspace_dir / rel
            return p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""

        for vertex in failed:
            v = h.vertices[vertex]
            path = self.workspace_dir / vertex.partition("#")[0]
            module = h.tested_module(vertex) if v.kind == "test" else vertex
            # The other side of the conflict: a failed test sees the module it tests, a failed module its tests.
            if v.kind == "test":
                counterpart = {module: _read(module)} if module else {}
            elif v.kind in ("code", "entry"):
                counterpart = {t: _read(t) for t in h.tests_of(vertex)}
            else:
                counterpart = {}
            now = error_signature(_latest_errors(v.history))
            prints = self.__dict__.setdefault("_replan_prints", {})
            same_error = bool(now) and prints.get(vertex) == now
            prints[vertex] = now
            entries.append({
                "same_error_as_last_round": same_error,
                "counterpart_files": {rel: src for rel, src in counterpart.items() if src},
                "dependencies": self._dependency_sources(h, vertex, _read),
                "dependents": self._dependent_sources(h, vertex, _read, set(counterpart)),
                "vertex": vertex,
                "kind": v.kind,
                "planned_interface": interfaces.get(module, "") if module else "",
                "current_content": path.read_text(encoding="utf-8", errors="replace") if path.is_file() and v.kind != "chapter" else "",
                "attempts": v.attempts,
                "failures": v.failures,
                "latest_errors": _latest_errors(v.history),
                "history": _history_before_latest(v.history),
                "last_writer": v.last_writer,
                "waiting_on_it": _dependents(h, vertex),
            })
        return {
            "failed": entries,
            "verified_do_not_touch": sorted(v for v, x in h.vertices.items() if x.state == "verified"),
            "entrypoint": blueprint.get("entrypoint"),
        }

    @staticmethod
    def _open_tasks_for_planner(state: _RunState) -> list[dict[str, Any]]:
        """Only the tasks that can still run: the finished ones (every `T*`, `D*`, `R*` of the run, with their tracebacks)
        were 21 of the 89 thousand characters of the planner's payload (§XXXVIII.2)."""
        return [{k: v for k, v in t.items() if k != "planned_description"} for t in state.tasks if t.get("status") in ("TODO", "WAITING")]

    @staticmethod
    def _interfaces_for_planner(h: Hypergraph, interfaces: dict[str, str], failed: list[str]) -> dict[str, str]:
        """The interfaces of the modules that did not fail, without bodies (the failed ones are in the dossier as
        `planned_interface`). Nothing when only chapters failed: no code interface is of use to them (§XXXVIII.2)."""
        if not any(h.vertices[v].kind in ("code", "entry", "test") for v in failed):
            return {}
        own = {h.tested_module(v) if h.vertices[v].kind == "test" else v for v in failed}
        return {rel: interface_view(src) for rel, src in interfaces.items() if rel not in own}

    def _redesign_due(self, h: Hypergraph) -> bool:
        """At least one local re-plan has run, and since then no vertex became verified that had not been before."""
        progress = self.__dict__.get("_replan_progress") or []
        ever = self.__dict__.get("_replan_ever_verified") or set()
        return bool(progress) and not ({v for v, x in h.vertices.items() if x.state == "verified"} - ever)

    def _replan_failed(self, state: _RunState) -> dict[str, Any] | None:
        """None when nothing failed; {"tasks": [...]} after a re-plan; {"stop": payload} when re-planning is spent."""
        failed = self._failed_vertices()
        if not failed:
            return None
        h = self._project_h()
        # The design may be what is wrong (§XXVIII.8), but only after the local re-plan had its round and the failed
        # vertices did not move (§XXX P4: at the end of the first wave the designer saw stubs and test errors and rebuilt
        # modules that only needed a repair). Such a round counts against none of the limits below. A round that cannot
        # be built falls through to the re-plan.
        if self._redesign_due(h):
            redesigned = self._redesign_failed(state, failed)
            if redesigned is not None:
                return redesigned
        progress = self.__dict__.setdefault("_replan_progress", [])
        # Progress = vertices that were ever verified: a deliberate reopening (or a figure crash undoing a verified file)
        # must not look like standing still (§XXVII: 01 stopped at [6, 7, 6] one line from a working environment.py).
        ever = self.__dict__.setdefault("_replan_ever_verified", set())
        ever.update(v for v, x in h.vertices.items() if x.state == "verified")
        progress.append(len(ever))
        stalled = len(progress) > REPLANS_WITHOUT_PROGRESS and progress[-1] <= progress[-1 - REPLANS_WITHOUT_PROGRESS]
        if stalled or len(progress) > MAX_REPLANS:
            return {"stop": self._replan_exhausted(state, failed)}

        blueprint = read_json_state(self.blueprint_path) if self.blueprint_path.exists() else {}
        interfaces = _plan_interfaces(blueprint)
        dossier = self._repair_dossier(h, failed)
        print(f"\n  [PRZEPLANOWANIE {len(progress)}] Nieudane wierzchołki: {', '.join(failed)}", flush=True)
        self.logger.log_step("REPLAN", f"Przeplanowanie nieudanych wierzchołków ({len(failed)})", {"failed": failed})
        answer = self._call_planning_agent(
            self.agents_dir / "planning" / "task_planner.md",
            {
                "user_prompt": self.current_user_prompt,
                "current_plan": {
                    "tasks": self._open_tasks_for_planner(state), "interfaces": self._interfaces_for_planner(h, interfaces, failed),
                    "academic_blueprint": {k: v for k, v in blueprint.items() if k not in ("literature_recon", "interfaces")},
                },
                "repair_dossier": dossier,
                "available_packages": sorted(available_package_imports().values()),
                "error_feedback": texts.replan_failed_instruction(failed, self.__dict__.get("_replan_uncovered") or []),
            },
        )
        out = answer.get("output") if answer.get("status") == "ok" else None
        out = out if isinstance(out, dict) else {}
        changed = self._replan_interfaces(h, out, failed, interfaces, blueprint, dossier)
        tasks, dropped, updated, reopened = self._replan_tasks(h, out, len(progress), state, self._reopenable(h, dossier))
        covered = {self._task_vertex(t) for t in state.tasks if t.get("status") in ("TODO", "WAITING")} | {self._task_vertex(t) for t in tasks}
        covered |= {str(g.get("vertex")) for g in out.get("gaps") or [] if isinstance(g, dict)}
        # A failed vertex whose own dependencies did not fail has no excuse to stay without a task or a gap
        # (2026-11-22: synth_data.py in 02 and q_agent.py in 01 were skipped round after round).
        uncovered = [v for v in failed if v not in covered and not readiness(h, v, set())]
        self._replan_uncovered = uncovered
        self.logger.log_event(
            "REPLANNED", round=len(progress), failed=failed, tasks=[t["task_id"] for t in tasks],
            interfaces_changed=changed, dropped=dropped, updated=updated, reopened=reopened,
            gaps=out.get("gaps") or [], uncovered=uncovered,
        )
        state.tasks.extend(tasks)
        write_json_state(self.task_queue_path, state.tasks)
        print(f"  [PRZEPLANOWANIE {len(progress)}] {len(tasks)} nowych zadań; zmienione interfejsy: {changed or '-'}", flush=True)
        return {"tasks": tasks}

    def _replan_interfaces(
        self, h: Hypergraph, out: dict[str, Any], failed: list[str], interfaces: dict[str, str], blueprint: dict[str, Any],
        dossier: dict[str, Any] | None = None,
    ) -> list[str]:
        """Interface changes of failed modules, each validated like the plan (`_apply_amendment`)."""
        allowed = {h.tested_module(v) if h.vertices[v].kind == "test" else v for v in failed}
        # An interface change is no answer to an error the last re-plan did not move (§XXX P9b, 01: rounds 2-4 rewrote the
        # interface of `game_loop.py` and `q_learning_agent.py` against an unchanged `.FF..` whose cause was a test).
        unchanged = {e["vertex"] for e in (dossier or {}).get("failed", []) if e.get("same_error_as_last_round")}
        changed: list[str] = []
        for rel, planned in _plan_interfaces(out).items():
            # An interface has no bodies (§XXXVII.6: the planner wrote 50-line implementations, with the very bugs of the
            # code, into `interfaces`, from where the next planner and the testers read them).
            source = interface_view(planned)
            if interface_view(interfaces.get(rel, "")) == source:
                continue
            if rel in unchanged:
                self.logger.log_event("SPEC_AMEND_SKIPPED", module=rel, task_id="REPLAN", reason="same error as after the last re-plan")
                continue
            if rel not in allowed or f"I:{rel}" not in h.edges:
                reason = "not a failed module" if f"I:{rel}" in h.edges else "not a module of the plan"
                self.logger.log_event("SPEC_AMEND_SKIPPED", module=rel, task_id="REPLAN", reason=reason)
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
        self, h: Hypergraph, out: dict[str, Any], round_no: int, state: _RunState, reopenable: set[str]
    ) -> tuple[list[dict[str, Any]], list[str], list[str], list[str]]:
        """New tasks of the re-plan: on vertices that are not verified, one per vertex. A vertex that already has an
        open task gets the new description there (2026-11-22, 01: the fix of a test waiting for its failed module was
        dropped as "already queued" and the module was rewritten four times against the wrong test). One verified
        module of the dossier may be reopened per round (`stale`), if it was not reopened before."""
        open_tasks = {self._task_vertex(t): t for t in state.tasks if t.get("status") in ("TODO", "WAITING")}
        tasks: list[dict[str, Any]] = []
        dropped: list[str] = []
        updated: list[str] = []
        reopened: list[str] = []
        for i, raw in enumerate(out.get("tasks") or [], 1):
            if not isinstance(raw, dict) or not raw.get("target_node"):
                dropped.append(str(raw)[:120])
                continue
            task = {
                "task_id": f"R{round_no}_{i}",
                "description": self._with_latest_errors(h, raw),
                "planned_description": str(raw.get("description") or ""),  # without the findings: they are read again when the task starts
                "target_node": str(raw["target_node"]),
                "assigned_agent": str(raw.get("assigned_agent") or ""),
                "status": "TODO",
            }
            vertex = self._task_vertex(task)
            if vertex is None:
                dropped.append(f"{task['target_node']}: not in the plan")
                continue
            if h.vertices[vertex].state == "verified":
                if vertex not in reopenable or reopened:
                    dropped.append(f"{task['target_node']}: verified")
                    continue
                self._set_vertex_state(vertex, "stale", task_id="REPLAN", by="REPLAN_REOPENED")
                self.__dict__.setdefault("_replan_reopened", set()).add(vertex)
                reopened.append(vertex)
            if h.vertices[vertex].kind == "test" and h.vertices.get(h.tested_module(vertex) or "") is not None                     and h.vertices[h.tested_module(vertex)].state == FAILED:
                task["force_ready"] = True  # once: the test is fixed first, the failed module is judged by the fixed test
            if vertex in open_tasks:
                open_tasks[vertex]["description"] = task["description"]
                open_tasks[vertex]["planned_description"] = task["planned_description"]
                if task.get("force_ready"):
                    open_tasks[vertex]["force_ready"] = True
                updated.append(vertex)
                continue
            task["assigned_agent"] = self._resolve_active_agent(task["assigned_agent"], fallback=_agent_for_path(vertex.partition("#")[0]))
            open_tasks[vertex] = task
            tasks.append(task)
        tasks.sort(key=lambda t: not t.get("force_ready"))
        return tasks, dropped, updated, reopened

    def _fresh_description(self, h: Hypergraph, task: dict[str, Any]) -> None:
        """A re-planned task that waited (a test goes first with `force_ready`, its module waits) carries the findings of
        the moment it was planned; its vertex may have failed differently since (§XXXVII.7: `R1_1` started with the hang
        of before `R1_2` had changed `environment.py`). They are read again when the task starts."""
        if (planned := task.get("planned_description")) is not None:
            task["description"] = self._with_latest_errors(h, {"description": planned, "target_node": task.get("target_node")})

    def _with_latest_errors(self, h: Hypergraph, raw: dict[str, Any]) -> str:
        """The planner's description plus, by the harness, the findings of the last verification of the vertex."""
        description = str(raw.get("description") or "")
        vertex = self._task_vertex({"target_node": str(raw.get("target_node") or "")})
        latest = _latest_errors(h.vertices[vertex].history) if vertex in h.vertices else []
        if not latest:
            return description
        return description + texts.replan_latest_errors([e[:LATEST_ERROR_CHARS] for e in latest])

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


