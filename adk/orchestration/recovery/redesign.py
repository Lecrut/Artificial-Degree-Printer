"""Redesign (§XXVIII.8): when the queue ended and modules failed after every repair, the design may be what is wrong,
and `verified` only says a file passed its own tests. The re-plan that touches only the failed (`fragment_replan`) has no
way back; this one has.

1. The audit says what every file of the project really does (`implementation_audit`).
2. The designer (`plan_outline` in revision mode) reads it with the plan and the unresolved errors, and answers a revised
   outline with a status for every module: keep, change, new or remove. Code checks the answer (`redesign_rules`).
3. The modules it changes or adds go through the planning stages again (`_converge`: `plan_module`, its critic, the main
   critic), the modules it keeps stay accepted and are only re-checked by code against their changed neighbours.
4. H is built again from the new plan and what the run knew about every vertex that was not redesigned is carried
   over; the tasks of what is not verified replace the waiting ones.

A round that fails at any step changes nothing and the re-plan of the failed (`task_planner`) takes over. At most
`MAX_REDESIGNS` rounds a run, and none of them counts against the limits of the re-plan."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from adk.core.models import read_json_state, write_json_state
from adk.hypergraph import Hypergraph, save
from adk.hypergraph.build import RESULTS_FILE
from adk.hypergraph.schedule import vertex_of
from adk.orchestration import agent_texts as texts
from adk.orchestration.common import _RunState, available_package_imports
from adk.orchestration.recovery.replan import _latest_errors
from adk.orchestration.recovery.implementation_audit import compact_audit
from adk.orchestration.planning.outline import module_files, outline_of, outline_view, outline_violations
from adk.orchestration.planning.phase import _existing_code
from adk.orchestration.recovery.redesign_rules import decisions_of, diagnosis_of, revision_violations, settled_decisions, sources_wanted
from adk.tools.building.experiment_runner import EXPERIMENT_TIMEOUT_S

MAX_REDESIGNS = 2  # rounds a run
REDESIGN_ANSWERS = 2  # answers of the designer per round: the first and one correction
ATTEMPTS_PER_ROUND = 2  # tries per round a run may spend, whether or not they end in a redesign
_RUN_ERROR_CHARS = 800
_ERRORS_PER_VERTEX = 3
SOURCES_CHARS = 8000  # of each file the designer asked to read


def _users_closure(h: Hypergraph, modules: set[str]) -> set[str]:
    """The modules that use any of `modules`, directly or through other modules."""
    found: set[str] = set()
    frontier = list(modules)
    while frontier:
        current = frontier.pop()
        for rel, vertex in h.vertices.items():
            if vertex.kind in ("code", "entry") and rel not in found and current in h.edges[f"I:{rel}"].spec.get("uses", {}):
                found.add(rel)
                frontier.append(rel)
    return found


def _carry_over(old: Hypergraph, new: Hypergraph, rebuild: set[str], failed: set[str]) -> None:
    """What the run knows of a vertex survives the new H unless the vertex itself is redesigned: its state, attempts,
    failures, history and writer. A vertex that failed starts again with its attempts (its failures stay: they decide the
    model); the tests of the modules that use a redesigned module are verified again; so are the results it can change."""
    redesigned_tests = {t for rel in rebuild for t in new.tests_of(rel)}
    stale = {t for rel in _users_closure(new, rebuild) - rebuild for t in new.tests_of(rel)}
    for vid, vertex in new.vertices.items():
        before = old.vertices.get(vid)
        if before is None:
            continue
        vertex.files = list(before.files)
        if vid in rebuild or vid in redesigned_tests:
            continue
        vertex.state, vertex.failures, vertex.last_writer = before.state, before.failures, before.last_writer
        vertex.attempts, vertex.history = (0 if vid in failed else before.attempts), list(before.history)
        if vid in stale and vertex.state == "verified":
            vertex.state = "stale"
    # A chapter that cites a redesigned module points at symbols that may be gone (§XXXVII.5: chapter 3 stayed `verified`
    # with `\ref_ast` to a module the redesign had rebuilt).
    for edge in old.edges.values():
        if edge.type == "N" and set(edge.observed) & rebuild:
            for vid, role in edge.members.items():
                if role == "X" and vid in new.vertices and new.vertices[vid].state == "verified":
                    new.vertices[vid].state = "stale"
    run, results = new.edges.get("R:run"), new.vertices.get(RESULTS_FILE)
    if run is not None and results is not None and results.state == "verified" and rebuild & set(run.members):
        results.state = "stale"


EARLIER_ROUNDS = 3  # rounds of its own decisions the designer is shown
_WHY_CHARS = 220


def _remembered(decisions: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    """What a round decided, for the next one: every module it changed, added or removed, with its reason."""
    return {rel: {"status": d["status"], "why": d["why"][:_WHY_CHARS]} for rel, d in decisions.items() if d["status"] != "keep"}


class RedesignMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

    @property
    def plan_outline_path(self) -> Path:
        return self.state_dir / "plan_outline.json"

    def _redesign_failed(self, state: _RunState, failed: list[str]) -> dict[str, Any] | None:
        """{"tasks": [...]} after a redesign; None when the re-plan of the failed is to take this round."""
        done, tried = self.__dict__.get("_redesigns", 0), self.__dict__.get("_redesign_attempts", 0)
        h, limit = self._project_h(), getattr(self, "max_redesigns", MAX_REDESIGNS)
        # An attempt that gives no usable guidelines costs the designer's answers and hands the round to the re-plan; the
        # same attempt every round would spend minutes on nothing, so the attempts are limited as well.
        if h is None or done >= limit or tried >= ATTEMPTS_PER_ROUND * limit:
            return None
        blueprint = read_json_state(self.blueprint_path) if self.blueprint_path.exists() else {}
        old = self._saved_outline(blueprint)
        if old is None:
            self.logger.log_event("REDESIGN_FALLBACK", reason="the outline of the plan is not saved")
            return None
        self.__dict__["_redesign_attempts"] = tried + 1
        print(f"\n  [PRZEPROJEKTOWANIE {done + 1}/{limit}] Nieudane wierzchołki: {', '.join(failed)}", flush=True)
        self.logger.log_event("REDESIGN_STARTED", round=done + 1, attempt=tried + 1, failed=failed)
        payload = self._redesign_payload(blueprint, old)
        guidelines = self._guidelines(payload, old, failed)
        if guidelines is None:
            self.logger.log_event("REDESIGN_FALLBACK", reason="no guidelines that pass the checks")
            return None
        new, decisions = guidelines
        earlier = {"round": done + 1, "attempt": tried + 1, "decisions": _remembered(decisions), "outcome": "not built"}
        self.__dict__.setdefault("_redesign_history", []).append(earlier)
        interfaces = blueprint.get("interfaces") if isinstance(blueprint.get("interfaces"), dict) else {}
        accepted = {rel: src for rel, src in interfaces.items() if rel in module_files(new)}
        reopen: dict[str, list[str]] = {}
        new = self._revise_outline(old, new, accepted, reopen)
        for rel, decision in decisions.items():
            if decision["status"] == "change" and rel in accepted:
                reopen[rel] = [*reopen.get(rel, []), texts.redesign_change_feedback(rel, decision["why"])]
        plan_out, planned, problems = self._converge(payload, {}, new, accepted, reopen)
        if problems:
            earlier["outcome"] = f"not built: {problems[0][:200]}"
            self.logger.log_event("REDESIGN_FALLBACK", reason="the redesigned plan cannot be built", problems=problems[:5])
            return None
        earlier["outcome"] = "applied; the modules it changed were built and the failures came back"
        tasks = self._apply_redesign(state, h, old, new, decisions, plan_out, planned, blueprint, set(failed), done + 1)
        self.__dict__["_redesigns"] = done + 1
        print(f"  [PRZEPROJEKTOWANIE {done + 1}] {len(tasks)} zadań w nowej kolejce", flush=True)
        return {"tasks": tasks}

    def _saved_outline(self, blueprint: dict[str, Any]) -> dict[str, Any] | None:
        """The outline in force, as planning saved it; None for a run planned before the outline was saved."""
        raw = read_json_state(self.plan_outline_path) if self.plan_outline_path.exists() else None
        outline = outline_of(raw) if isinstance(raw, dict) and raw else None
        if outline is not None:
            outline["thesis_type"], outline["template_name"] = blueprint.get("thesis_type"), blueprint.get("template_name")
        return outline

    def _redesign_payload(self, blueprint: dict[str, Any], old: dict[str, Any]) -> dict[str, Any]:
        """What planning sends its agents, as far as a redesign needs it."""
        return {
            "user_prompt": self.current_user_prompt,
            "include_docs": self.include_docs,
            "available_packages": sorted(available_package_imports().values()),
            "experiment_time_limit_s": EXPERIMENT_TIMEOUT_S,
            "detected_template": {"thesis_type": blueprint.get("thesis_type"), "is_certain": True},
            "missing_agent_specialization": old.get("missing_agent_specialization"),
        }

    def _guidelines(
        self, payload: dict[str, Any], old: dict[str, Any], failed: list[str]
    ) -> tuple[dict[str, Any], dict[str, dict[str, str]]] | None:
        """(the revised outline, a status for every module) that code accepts, or None. The designer sees the audit
        and the errors, no body; it has one correction, and once a round it may ask to read the code of up to
        `MAX_SOURCE_FILES` files (an answer that only asks costs no correction)."""
        h = self._project_h()
        run_error = str(getattr(self, "_last_experiment_error", "") or "")
        audit = self._implementation_audit(failed)
        revision: dict[str, Any] = {
            "reason": texts.redesign_reason(failed), "failed": failed,
            "implementation": compact_audit(audit),
            "unresolved_errors": {v: [e[:600] for e in _latest_errors(h.vertices[v].history)[:_ERRORS_PER_VERTEX]] for v in failed},
            **({"run_error": run_error[:_RUN_ERROR_CHARS]} if run_error else {}),
        }
        if earlier := self.__dict__.get("_redesign_history"):
            # §XXXI P2: without its own earlier decisions the designer turned "string states" of round 1 into "numpy arrays"
            # in round 2, and both were built.
            revision["earlier_rounds"] = earlier[-EARLIER_ROUNDS:]
        readable = {rel for rel, card in audit["files"].items() if card["implemented"]}
        workspace = set(_existing_code(self.workspace_dir, limit=None))
        feedback: list[str] = []
        asked, attempt, previous = False, 0, None
        while attempt < REDESIGN_ANSWERS:
            answer = self._call_planning_agent(self.agents_dir / "planning" / "plan_outline.md", {
                **payload, "current_outline": outline_view(old), "revision": revision,
                **({"feedback": feedback} if feedback else {}), **({"previous_outline": previous} if previous and feedback else {}),
            })
            output = answer.get("output") if answer.get("status") == "ok" else None
            if not asked and (wanted := sources_wanted(output, readable)):
                asked = True
                revision["sources"] = {rel: (self.workspace_dir / rel).read_text(encoding="utf-8", errors="replace")[:SOURCES_CHARS] for rel in wanted}
                self.logger.log_event("REDESIGN_SOURCE_GRANTED", files=wanted)
                continue
            attempt += 1
            candidate = outline_of(output)
            if candidate is None:
                feedback = [texts.OUTLINE_NO_MODULES]
                self.logger.log_event("REDESIGN_GUIDELINES", attempt=attempt, problems=feedback)
                continue
            candidate["thesis_type"], candidate["template_name"] = old.get("thesis_type"), old.get("template_name")
            previous = outline_view(candidate)
            candidate, decisions = settled_decisions(old, candidate, decisions_of(output), set(failed))
            problems = outline_violations(candidate, {}, bool(self.include_docs)) + revision_violations(old, candidate, decisions, workspace)
            self.logger.log_event(
                "REDESIGN_GUIDELINES", attempt=attempt, decisions=decisions, diagnosis=diagnosis_of(output), problems=problems,
            )
            if not problems:
                return candidate, decisions
            feedback = problems
        return None

    def _apply_redesign(
        self, state: _RunState, old_h: Hypergraph, old: dict[str, Any], new: dict[str, Any], decisions: dict[str, dict[str, str]],
        plan_out: dict[str, Any], interfaces: dict[str, str], blueprint: dict[str, Any], failed: set[str], round_no: int,
    ) -> list[dict[str, Any]]:
        """The redesigned plan becomes the project: files of removed modules go, the blueprint and the outline are saved,
        H is built from the new plan with what the run knew carried over, and the queue holds what is not verified."""
        before = blueprint.get("interfaces") if isinstance(blueprint.get("interfaces"), dict) else {}
        removed = set(module_files(old)) - set(module_files(new))
        rebuild = {
            rel for rel in module_files(new)
            if rel not in before or interfaces.get(rel) != before.get(rel) or decisions.get(rel, {}).get("status") in ("change", "new")
        }
        for rel in sorted(removed):
            paths = [*old_h.files_of(rel), *(p for test in old_h.tests_of(rel) for p in old_h.files_of(test))]
            for path in paths:
                (self.workspace_dir / path).unlink(missing_ok=True)
            self.logger.log_event("REDESIGN_REMOVED", module=rel, files=paths)
        merged = {**blueprint, **plan_out["academic_blueprint"], "interfaces": interfaces}
        if isinstance(merged.get("planned_chapters"), list):
            merged["table_of_contents"] = {"chapters": merged["planned_chapters"]}
        write_json_state(self.blueprint_path, merged)
        write_json_state(self.plan_outline_path, outline_view(new))
        self.hypergraph = None  # the stubs of new modules are written against the H just built, which the gate loads
        h = self._build_project_hypergraph(interfaces, merged, plan_out["tasks"])
        self.hypergraph = h
        _carry_over(old_h, h, rebuild, failed)
        for rel in sorted(rebuild):
            self._reopen_test_review(h, rel)
        save(h, self.hypergraph_path)
        tasks: list[dict[str, Any]] = []
        for task in plan_out["tasks"]:
            vertex = vertex_of(h, str(task.get("target_node", "")), str(task.get("description", "")))
            if vertex is not None and h.vertices[vertex].state != "verified":
                tasks.append({**task, "task_id": f"D{round_no}_{len(tasks) + 1}", "status": "TODO"})
        state.tasks[:] = [t for t in state.tasks if t.get("status") not in ("TODO", "WAITING")] + tasks
        write_json_state(self.task_queue_path, state.tasks)
        self.logger.log_event(
            "REDESIGN_APPLIED", round=round_no, redesigned=sorted(rebuild), removed=sorted(removed),
            kept=sorted(set(module_files(new)) - rebuild), tasks=[t["task_id"] for t in tasks],
        )
        return tasks
