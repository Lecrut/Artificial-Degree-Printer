"""Planning in stages (§XVI, 2026-11-21). One plan grows through four stages; nothing ever goes back to the start.

1. Outline (`plan_outline.md`): modules with purpose, dependencies and promised names, entrypoint, figures, metrics,
   chapters. Checked by code (`plan_outline.outline_violations`), then by its critic (`outline_critic_guard.md`).
2. Interfaces, one module at a time, dependencies first (`plan_module.md`): each sees the accepted interfaces it
   builds on, is checked by code against them, then by its critic (`module_critic_guard.md`). Accepted = frozen.
3. Tasks: derived by code from the outline and the interfaces (`plan_tasks`).
4. Fusion: the whole plan checked by code and by the main critic (`plan_critic_guard.md`).

A finding names the part it is about, and only that part is reopened: a module (its dependents are then re-checked
by code and reopened only if they broke) or the outline (then only the modules whose outline entry changed). A module
may ask its dependency for what it lacks (`needs`). Every loop has a budget; a module that cannot converge escalates
once to the outline; after the main critic's rounds an executable plan goes on with the objections logged."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from adk.hypergraph.validate import code_violations
from adk.orchestration import agent_texts as texts
from adk.orchestration.plan_existing import _with_existing
from adk.orchestration.plan_outline import (
    changed_modules, dependents, existing_names, kept_as_is, module_entry, module_files, module_order, outline_of, outline_view,
    outline_violations, provided_name,
)
from adk.orchestration.plan_spec import interface_view, plan_targets
from adk.orchestration.plan_tasks import planned_tasks
from adk.orchestration.planning import _existing_code
from adk.tools.verification.contract_check import stub_source

OUTLINE_ROUNDS = 3  # answers of the outline author per outline stage (first answer + corrections)
OUTLINE_CRITIC_ROUNDS = 2  # of them, rounds the outline critic may block
MODULE_ROUNDS = 3  # answers of the module author per module stage
MODULE_CRITIC_ROUNDS = 1
FINAL_ROUNDS = 2  # main-critic rounds that may send parts back; then an executable plan goes on
NEEDS_BUDGET = 2  # requests of a module for more from an accepted dependency, per plan
ESCALATIONS = 1  # a module that cannot converge sends its evidence to the outline this many times

_PLACE = re.compile(r"\[([^\]]+)\]")
_MODULE_KEYS = ("user_prompt", "available_packages", "experiment_time_limit_s")


def _route(findings: list[str], files: list[str]) -> tuple[dict[str, list[str]], list[str]]:
    """(findings per planned module, findings for the outline) by the place each one names."""
    by_module: dict[str, list[str]] = {}
    rest: list[str] = []
    for text in findings:
        match = _PLACE.search(text)
        place = (match.group(1) if match else "").lower()
        rel = next((r for r in sorted(files, key=len, reverse=True) if r.lower() in place or Path(r).name.lower() in place), None)
        if rel:
            by_module.setdefault(rel, []).append(text)
        else:
            rest.append(text)
    return by_module, rest


_FENCE = re.compile(r"^\s*```(?:python|py)?\s*\n(.*?)\n?```\s*$", re.S)


def _module_source(output: Any, rel: str) -> str:
    """The interface a module author returned, as Python: a markdown fence is taken off, and a single line with
    literal `\\n` escapes (a model does that) becomes lines."""
    if not isinstance(output, dict):
        return ""
    interfaces = output.get("interfaces") if isinstance(output.get("interfaces"), dict) else {}
    source = output.get("source") or output.get("interface") or output.get("code") or interfaces.get(rel)
    if not isinstance(source, str) or not source.strip():
        return ""
    if fenced := _FENCE.match(source):
        source = fenced.group(1)
    if "\\n" in source and "\n" not in source.strip():
        source = source.replace("\\n", "\n").replace('\\"', '"')
    return source


class PlanStagesMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

    def _staged_plan(self, plan_payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str], list[str]]:
        """(plan, its interfaces, blockers): the plan built stage by stage; blockers only when it cannot be built."""
        existing = _existing_code(self.workspace_dir, limit=None)
        outline, problems = self._outline_stage(plan_payload, existing, None, [])
        if outline is None:
            return {}, {}, problems
        accepted: dict[str, str] = {}
        reopen: dict[str, list[str]] = {}
        history: list[dict[str, Any]] = []
        escalations, fusion = ESCALATIONS, 0
        while True:
            ok, failed, problems = self._settle(plan_payload, outline, accepted, existing, reopen)
            if not ok:
                revised = None
                if escalations > 0:
                    escalations -= 1
                    revised, _ = self._outline_stage(plan_payload, existing, outline, [texts.module_cannot_settle(failed, problems)])
                if revised is None:
                    return {}, {}, problems
                outline = self._revise_outline(outline, revised, accepted, reopen)
                continue
            plan_out, interfaces = self._fused(outline, accepted, existing, plan_payload)
            code = code_violations(interfaces, outline["entrypoint"], outline["plots"], outline["academic_blueprint"].get("metrics"))[1]
            critic, warnings = ([], []) if code else self._plan_review(plan_out, interfaces, plan_payload, history)
            self.logger.log_event(
                "PLAN_CHECKED", attempt=fusion, modules=sorted(interfaces),
                blockers={"code": [str(v) for v in code], "critic": critic}, warnings=warnings,
            )
            if not code and not critic:
                print(f"  [PLAN 4/4: KRYTYK GŁÓWNY] plan przyjęty ({len(interfaces)} modułów, {len(plan_out['tasks'])} zadań)", flush=True)
                return plan_out, interfaces, []
            if fusion >= FINAL_ROUNDS:
                if code:
                    return plan_out, interfaces, [str(v) for v in code]
                # Every check by code passes: the plan is executable. The critic's remaining objections are opinions the
                # build (verification, controlled plan change) can still settle (decision of 2026-11-21, §XV.11).
                self.logger.log_event("PLAN_ACCEPTED_OVER_CRITIC", critic=critic)
                print(f"  [PLAN 4/4: KRYTYK GŁÓWNY] plan przyjęty mimo {len(critic)} zastrzeżeń (w logu)", flush=True)
                return plan_out, interfaces, []
            fusion += 1
            history.append({"round": fusion, "blockers": critic + [str(v) for v in code]})
            by_module, for_outline = _route(critic, module_files(outline))
            for rel, findings in by_module.items():
                self._learn_from_critic("plan_module", rel, findings)
            self._learn_from_critic("plan_outline", f"outline:{len(self._critic_log)}", for_outline)
            for v in code:
                if v.culprit in accepted:
                    by_module.setdefault(v.culprit, []).append(str(v))
                else:
                    for_outline.append(str(v))
            for rel, findings in by_module.items():
                reopen[rel] = reopen.get(rel, []) + findings
            print(
                f"  [PLAN 4/4: KRYTYK GŁÓWNY] runda {fusion}/{FINAL_ROUNDS}: ponownie "
                + ", ".join([*by_module, *(["szkic"] if for_outline else [])]), flush=True,
            )
            if for_outline:
                revised, _ = self._outline_stage(plan_payload, existing, outline, for_outline)
                if revised is not None:
                    outline = self._revise_outline(outline, revised, accepted, reopen)
                else:
                    self.logger.log_event("PLAN_OUTLINE_KEPT", findings=for_outline)

    # --- stage 1: outline ---------------------------------------------------------------------------------------

    def _outline_stage(
        self, plan_payload: dict[str, Any], existing: dict[str, str], current: dict[str, Any] | None, feedback: list[str]
    ) -> tuple[dict[str, Any] | None, list[str]]:
        """(the accepted outline, []) or (None, its last problems). With `current`, a revision of that outline."""
        outline, fb, critic_left = current, list(feedback), OUTLINE_CRITIC_ROUNDS
        history: list[dict[str, Any]] = []
        for attempt in range(1, OUTLINE_ROUNDS + 1):
            payload = {**plan_payload, **({"current_outline": outline_view(outline)} if outline else {}), **({"feedback": fb} if fb else {})}
            answer = self._call_planning_agent(self.agents_dir / "planning" / "plan_outline.md", payload)
            candidate = outline_of(answer.get("output") if answer.get("status") == "ok" else None)
            if candidate is None:
                fb = [texts.OUTLINE_NO_MODULES]
                self.logger.log_event("PLAN_OUTLINE_CHECKED", attempt=attempt, modules=[], problems=fb, critic=[])
                continue
            problems = outline_violations(candidate, existing, bool(self.include_docs))
            critic: list[str] = []
            if not problems and critic_left and attempt < OUTLINE_ROUNDS:
                verdict = self._critic_review("outline_critic_guard.md", {
                    "user_prompt": plan_payload.get("user_prompt", ""), "outline": outline_view(candidate),
                    "existing_files": sorted(existing), "review_history": history,
                }, plan_targets(module_files(candidate)))
                critic = verdict[0] if verdict else []
                if critic:
                    critic_left -= 1
                    history.append({"round": attempt, "blockers": critic})
                    self._learn_from_critic("plan_outline", f"outline:{len(self._critic_log)}", critic)
            self.logger.log_event("PLAN_OUTLINE_CHECKED", attempt=attempt, modules=module_files(candidate), problems=problems, critic=critic)
            outline = candidate
            if problems or critic:
                fb = problems + critic
                print(f"  [PLAN 1/4: SZKIC] poprawka {attempt}: {len(problems)} problemów, {len(critic)} blokad krytyka", flush=True)
                continue
            order = module_order(candidate)
            self.logger.log_event("PLAN_OUTLINE_ACCEPTED", attempts=attempt, order=order, revision=current is not None)
            print(f"  [PLAN 1/4: SZKIC] przyjęty: {', '.join(order)}", flush=True)
            return candidate, []
        return None, fb

    def _revise_outline(
        self, old: dict[str, Any], new: dict[str, Any], accepted: dict[str, str], reopen: dict[str, list[str]]
    ) -> dict[str, Any]:
        """Adopt a revised outline: removed modules leave, accepted modules whose entry changed are reopened, the
        rest stays accepted."""
        changed, removed = changed_modules(old, new)
        for rel in removed:
            accepted.pop(rel, None)
            reopen.pop(rel, None)
        for rel in changed & set(accepted):
            reopen[rel] = reopen.get(rel, []) + [texts.outline_changed(rel)]
        self.logger.log_event("PLAN_OUTLINE_REVISED", changed=sorted(changed), removed=sorted(removed))
        return new

    # --- stage 2: interfaces ------------------------------------------------------------------------------------

    def _settle(
        self, plan_payload: dict[str, Any], outline: dict[str, Any], accepted: dict[str, str], existing: dict[str, str],
        reopen: dict[str, list[str]],
    ) -> tuple[bool, str, list[str]]:
        """Bring every module of the outline to an accepted interface, dependencies first: (converged, the module that
        could not converge, its last problems). An accepted module is re-checked by code (its dependencies may have
        changed) and redesigned only if it broke or a finding is about it."""
        for rel in [r for r in accepted if r not in module_files(outline)]:
            accepted.pop(rel)
        needs_left, restart, drafts = NEEDS_BUDGET, True, {}  # drafts: what a module wrote before it asked for more
        while restart:
            restart = False
            for rel in module_order(outline):
                feedback = reopen.pop(rel, None)
                if feedback is None and rel not in accepted and kept_as_is(outline, rel, existing):
                    accepted[rel] = existing[rel]  # code that is already there is its own interface
                    continue
                if rel in accepted and feedback is None:
                    live = {r: s for r, s in accepted.items() if r not in reopen}
                    feedback = self._module_problems(rel, accepted[rel], live, outline, existing) or None
                    if feedback is None:
                        continue
                if rel in accepted:
                    self.logger.log_event("PLAN_MODULE_REOPENED", module=rel, reasons=feedback)
                    feedback = texts.module_reopened(rel, feedback)
                live = {r: s for r, s in accepted.items() if r not in reopen}
                result = self._module_stage(
                    plan_payload, outline, rel, live, existing, feedback or [],
                    drafts.pop(rel, None) or accepted.get(rel) or existing.get(rel),
                )
                needs = {d: n for d, n in result["needs"].items() if d in accepted}
                if needs and needs_left > 0 and not result["ok"]:
                    needs_left -= 1
                    for dep, need in needs.items():
                        reopen[dep] = reopen.get(dep, []) + [texts.dependency_needs(rel, need)]
                    drafts[rel] = result["source"]
                    reopen[rel] = [texts.needs_granted(sorted(needs))]
                    self.logger.log_event("PLAN_MODULE_NEEDS", module=rel, needs=needs)
                    restart = True
                    break
                if not result["ok"]:
                    return False, rel, result["problems"]
                accepted[rel] = result["source"]
        return True, "", []

    def _module_stage(
        self, plan_payload: dict[str, Any], outline: dict[str, Any], rel: str, accepted: dict[str, str],
        existing: dict[str, str], feedback: list[str], previous: str | None,
    ) -> dict[str, Any]:
        """One module's interface: written, checked by code, reviewed; `{ok, source, problems, needs}`."""
        entry = module_entry(outline, rel)
        # An existing module the outline lists as a dependency but does not plan is still the author's to see.
        deps = {d: accepted.get(d) or existing[d] for d in self._dependency_closure(outline, rel) if d in accepted or d in existing}
        consumers = [module_entry(outline, c) for c in dependents(outline, rel)]
        fb, source, critic_left, objections = list(feedback), previous or "", MODULE_CRITIC_ROUNDS, []
        for attempt in range(1, MODULE_ROUNDS + 1):
            answer = self._call_planning_agent(self.agents_dir / "planning" / "plan_module.md", {
                **{k: plan_payload.get(k) for k in _MODULE_KEYS}, "outline": outline_view(outline), "module": entry,
                "dependencies": deps, "consumers": consumers,
                **({"previous_source": source} if source else {}), **({"feedback": fb} if fb else {}),
            })
            output = answer.get("output") if answer.get("status") == "ok" else None
            raw_needs = output.get("needs") if isinstance(output, dict) and isinstance(output.get("needs"), dict) else {}
            needs = {str(d): str(n) for d, n in raw_needs.items() if str(n).strip() and str(d) in entry["depends_on"]}
            new = _module_source(output, rel)
            if not new:
                fb = [texts.MODULE_NO_SOURCE]
                self.logger.log_event("PLAN_MODULE_CHECKED", module=rel, attempt=attempt, problems=fb, critic=[])
                continue
            source = new
            problems = self._module_problems(rel, source, accepted, outline, existing)
            if problems and needs:
                return {"ok": False, "source": source, "problems": problems, "needs": needs}
            critic: list[str] = []
            if not problems and critic_left and attempt < MODULE_ROUNDS:
                verdict = self._critic_review("module_critic_guard.md", {
                    "user_prompt": plan_payload.get("user_prompt", ""), "outline": outline_view(outline), "module": entry,
                    # The critic reviews the interface: a body the author wrote anyway is not shown to it (2026-11-21, 02:
                    # blockers on `import csv` and an attribute set inside a body that the coder rewrites).
                    "source": interface_view(source), "dependencies": deps, "consumers": consumers,
                }, {rel, Path(rel).name})
                critic = verdict[0] if verdict else []
                if critic:
                    critic_left -= 1
                    objections = critic
                    self._learn_from_critic("plan_module", rel, critic)
            self.logger.log_event("PLAN_MODULE_CHECKED", module=rel, attempt=attempt, problems=problems, critic=critic)
            if problems or critic:
                fb = problems + critic
                print(f"  [PLAN 2/4: INTERFEJS {rel}] poprawka {attempt}: {len(problems)} problemów, {len(critic)} blokad krytyka", flush=True)
                continue
            self.logger.log_event("PLAN_MODULE_ACCEPTED", module=rel, attempts=attempt, over_critic=objections if attempt > 1 else [])
            print(f"  [PLAN 2/4: INTERFEJS {rel}] przyjęty (próby: {attempt})", flush=True)
            return {"ok": True, "source": source, "problems": [], "needs": needs}
        print(f"  [PLAN 2/4: INTERFEJS {rel}] nie udało się: {len(fb)} problemów", flush=True)
        return {"ok": False, "source": source, "problems": fb, "needs": {}}

    @staticmethod
    def _dependency_closure(outline: dict[str, Any], rel: str) -> list[str]:
        seen: list[str] = []
        frontier = list(module_entry(outline, rel)["depends_on"])
        while frontier:
            dep = frontier.pop()
            if dep not in seen:
                seen.append(dep)
                frontier += module_entry(outline, dep)["depends_on"]
        return seen

    def _module_problems(
        self, rel: str, source: str, accepted: dict[str, str], outline: dict[str, Any], existing: dict[str, str]
    ) -> list[str]:
        """What code finds wrong with `source` as the interface of `rel`, next to the accepted interfaces: its stub,
        imports, constants, the harness's calls, the promised names, and the names accepted
        consumers already import from it."""
        if stub_source(source) is None:
            return [str(v) for v in code_violations({rel: source}, None)[1] if v.rule == "INTERFACE_DOES_NOT_PARSE"] or [texts.MODULE_NO_SOURCE]
        subset = _with_existing({"interfaces": {**{r: s for r, s in accepted.items() if r != rel}, rel: source}}, existing)["interfaces"]
        # Findings about other modules (e.g. the entrypoint's module not designed yet) belong to their own stage.
        specs, found = code_violations(subset, outline["entrypoint"], outline["plots"], outline["academic_blueprint"].get("metrics"))
        problems = [str(v) for v in found if (v.culprit or v.vertex) == rel]
        symbols = specs.get(rel, {}).get("symbols", {})
        if rel in specs:
            missing = [n for p in module_entry(outline, rel)["provides"] if (n := provided_name(p)) and n not in symbols]
            if missing:
                problems.append(texts.module_misses_provides(rel, missing))
            # Only what the outline promises is protected: a consumer that imports another name (it was designed against
            # an older outline, or invented it) is reopened at its own turn by `USES_UNDECLARED`. Protecting it here
            # left the author of a changed module with no right answer (2026-11-22, 01: the outline dropped
            # `evaluate_random_agent`, the accepted entrypoint still imported it, six attempts, plan rejected).
            promised = {provided_name(p).partition(".")[0] for p in module_entry(outline, rel)["provides"]}
            for other, spec in specs.items():
                used = [n for n in spec["uses"].get(rel, []) if n not in symbols and n != "*" and n in promised]
                if other != rel and used:
                    problems.append(texts.module_breaks_consumer(rel, other, used))
            dropped = sorted(existing_names(rel, existing[rel]) - set(symbols)) if rel in existing else []
            if dropped:
                problems.append(texts.module_drops_existing(rel, dropped, existing[rel]))
        return list(dict.fromkeys(problems))

    # --- stages 3 and 4: tasks and fusion -----------------------------------------------------------------------

    def _fused(
        self, outline: dict[str, Any], accepted: dict[str, str], existing: dict[str, str], plan_payload: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, str]]:
        """The whole plan from the outline, the accepted interfaces and the tasks derived from them."""
        files = module_files(outline)
        interfaces = _with_existing({"interfaces": {r: accepted[r] for r in files if r in accepted}}, existing)["interfaces"]
        detected = plan_payload.get("detected_template") if isinstance(plan_payload.get("detected_template"), dict) else {}
        thesis_type = str(
            (detected.get("thesis_type") if detected.get("is_certain") else None) or outline.get("thesis_type")
            or detected.get("thesis_type") or "inzynierska"
        )
        kept = {r for r in existing if interfaces.get(r) == existing[r]}
        # The specialist (from the outline, or asked for by the caller) implements the modules, once Layer 4 can create it.
        specialist = (outline.get("missing_agent_specialization") or plan_payload.get("missing_agent_specialization")) if self.enable_layer4 else None
        outline = {**outline, "missing_agent_specialization": specialist}
        tasks = planned_tasks(outline, interfaces, thesis_type, bool(self.include_docs), kept)
        blueprint = {**outline["academic_blueprint"], "entrypoint": outline["entrypoint"], "plots": outline["plots"]}
        plan_out = {
            "tasks": tasks, "interfaces": interfaces, "entrypoint": outline["entrypoint"], "academic_blueprint": blueprint,
            "thesis_type": outline.get("thesis_type"), "template_name": outline.get("template_name"),
            "missing_agent_specialization": specialist, "outline": outline_view(outline),
        }
        self.logger.log_event("PLAN_FUSED", modules=sorted(interfaces), tasks=len(tasks))
        print(f"  [PLAN 3/4: ZADANIA] {len(tasks)} zadań z {len(interfaces)} modułów i {len(blueprint.get('planned_chapters') or [])} rozdziałów", flush=True)
        return plan_out, interfaces
