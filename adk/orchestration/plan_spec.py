"""The plan as specification: validate the code part of the plan before any code exists, then build H and write
the stubs of σ (Audit VI §VII.12.6, A3). Replaces the single interface retry and the SKELETON task."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from adk.core.models import read_json_state
from adk.hypergraph import Hypergraph, build_from_plan, code_violations, save
from adk.orchestration import agent_texts as texts
from adk.orchestration.plan_interfaces import _interface_gaps, _plan_interfaces
from adk.tools.verification.contract_check import stub_source

CODE_PATCH_BUDGET = 4
CRITIC_PATCH_BUDGET = 4
MAX_PLANNER_PATCHES = 6
NO_PROGRESS_LIMIT = 2


def _entrypoint(plan_out: dict[str, Any]) -> str:
    blueprint = plan_out.get("academic_blueprint") if isinstance(plan_out.get("academic_blueprint"), dict) else {}
    return str(blueprint.get("entrypoint") or plan_out.get("entrypoint") or "").strip()


def _static_blockers(plan_out: dict[str, Any], interfaces: dict[str, str]) -> tuple[list[str], list[str]]:
    """(blocker_code, blocker_instruction): code/stub errors and task-vs-interface mismatches, each once."""
    blocker_code = (
        [str(v) for v in code_violations(interfaces, _entrypoint(plan_out))[1]]
        if interfaces
        else [texts.PLAN_WITHOUT_INTERFACES]
    )
    if not plan_out.get("tasks"):
        blocker_code.append(texts.PLAN_WITHOUT_TASKS)
    blocker_instruction = _interface_gaps(plan_out.get("tasks") or [], interfaces)
    return list(dict.fromkeys(blocker_code)), list(dict.fromkeys(blocker_instruction))


def _plan_view(plan_out: dict[str, Any], interfaces: dict[str, str]) -> dict[str, Any]:
    """The plan as the planner corrects it."""
    blueprint = plan_out.get("academic_blueprint") if isinstance(plan_out.get("academic_blueprint"), dict) else {}
    return {
        "tasks": plan_out.get("tasks") or [],
        "interfaces": interfaces,
        "entrypoint": _entrypoint(plan_out),
        "academic_blueprint": {k: v for k, v in blueprint.items() if k not in ("literature_recon", "interfaces")},
        "missing_agent_specialization": plan_out.get("missing_agent_specialization"),
    }


def _apply_patch(
    plan_out: dict[str, Any], interfaces: dict[str, str], patch: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    """(the plan with the patch applied, what the patch changed). A patch carries only what changes: `interfaces`
    (full source of each changed or new module), `remove_interfaces`, `entrypoint`, `academic_blueprint` fields,
    `tasks` (the whole list), `missing_agent_specialization`. Everything else stays as it was."""
    changed: list[str] = []
    merged = dict(interfaces)
    for rel, source in _plan_interfaces(patch).items():
        if merged.get(rel) != source:
            merged[rel] = source
            changed.append(rel)
    for raw in patch.get("remove_interfaces") or []:
        rel = str(raw).replace("\\", "/").removeprefix("./")
        if merged.pop(rel, None) is not None:
            changed.append(f"-{rel}")
    blueprint = dict(plan_out.get("academic_blueprint") if isinstance(plan_out.get("academic_blueprint"), dict) else {})
    blueprint.pop("interfaces", None)
    patch_blueprint = patch.get("academic_blueprint") if isinstance(patch.get("academic_blueprint"), dict) else {}
    for key, value in patch_blueprint.items():
        if key not in ("interfaces", "entrypoint") and blueprint.get(key) != value:
            blueprint[key] = value
            changed.append(f"academic_blueprint.{key}")
    entry = _entrypoint(plan_out)
    new_entry = str(patch.get("entrypoint") or patch_blueprint.get("entrypoint") or "").strip()
    if new_entry and new_entry != entry:
        entry = new_entry
        changed.append("entrypoint")
    blueprint["entrypoint"] = entry
    tasks = list(plan_out.get("tasks") or [])
    raw_tasks = patch.get("tasks")
    if isinstance(raw_tasks, dict) and raw_tasks:
        by_id = {str(t.get("task_id")): i for i, t in enumerate(tasks) if isinstance(t, dict) and t.get("task_id")}
        tasks_changed = False
        for tid, updates in raw_tasks.items():
            if tid in by_id and isinstance(updates, dict):
                idx = by_id[tid]
                updated = {**tasks[idx], **updates}
                if updated != tasks[idx]:
                    tasks[idx] = updated
                    tasks_changed = True
        if tasks_changed:
            changed.append("tasks")
    elif isinstance(raw_tasks, list) and raw_tasks and raw_tasks != tasks:
        tasks = raw_tasks
        changed.append("tasks")
    candidate = {**plan_out, "tasks": tasks, "interfaces": merged, "entrypoint": entry, "academic_blueprint": blueprint}
    if patch.get("missing_agent_specialization") and patch["missing_agent_specialization"] != plan_out.get("missing_agent_specialization"):
        candidate["missing_agent_specialization"] = patch["missing_agent_specialization"]
        changed.append("missing_agent_specialization")
    return candidate, changed


def _is_proven_blocker(issue: dict[str, Any], plan_out: dict[str, Any], interfaces: dict[str, str]) -> bool:
    """A critic blocker must name an existing target in the plan (`where`), a concrete failure (`problem`), and a fix."""
    where = str(issue.get("where") or "").strip()
    problem = str(issue.get("problem") or "").strip()
    fix = str(issue.get("fix") or "").strip()
    if not (where and problem and fix):
        return False
    where_l = where.lower()
    targets: set[str] = {"academic_blueprint", "entrypoint", "tasks", "interfaces", "missing_agent_specialization"}
    for rel in interfaces:
        targets.add(rel.lower())
        targets.add(Path(rel).name.lower())
    for task in plan_out.get("tasks") or []:
        if isinstance(task, dict) and task.get("task_id"):
            targets.add(str(task["task_id"]).lower())
    return any(t in where_l for t in targets)


def _apply_patch_with_partial_fallback(
    plan_out: dict[str, Any],
    interfaces: dict[str, str],
    patch: dict[str, Any],
    before_static: list[str],
    has_critic_blockers: bool,
) -> tuple[dict[str, Any], dict[str, str], list[str], list[str], bool, list[str], list[str], list[str], list[str]]:
    """Apply `patch` as a whole if it improves or preserves static checks; otherwise keep only the per-module
    changes that do not regress, returning `(plan, interfaces, blocker_code, blocker_instruction, accepted, changed, fixed, new, rejected)`."""
    before = set(before_static)
    candidate, changed = _apply_patch(plan_out, interfaces, patch)
    c_ifaces = _plan_interfaces(candidate)
    c_code, c_instr = _static_blockers(candidate, c_ifaces)
    after = set(c_code + c_instr)
    fixed, new = sorted(before - after), sorted(after - before)
    credit = len(fixed) + (1 if has_critic_blockers else 0)
    if changed and (not new or len(new) < credit):
        return candidate, c_ifaces, c_code, c_instr, True, changed, fixed, new, []
    if not changed:
        return plan_out, interfaces, [], [], False, [], [], [], [texts.PATCH_CHANGED_NOTHING]

    # Partial acceptance: keep non-regressing parts (e.g. valid module edits) and reject only what broke.
    cur_plan, cur_ifaces = plan_out, interfaces
    cur_static = set(before_static)
    cur_code, cur_instr = _static_blockers(cur_plan, cur_ifaces)
    partial_changed: list[str] = []
    rejected_notes: list[str] = []

    non_iface_patch = {k: v for k, v in patch.items() if k != "interfaces"}
    if non_iface_patch:
        t_plan, t_changed = _apply_patch(cur_plan, cur_ifaces, non_iface_patch)
        if t_changed:
            t_ifaces = _plan_interfaces(t_plan)
            t_code, t_instr = _static_blockers(t_plan, t_ifaces)
            t_after = set(t_code + t_instr)
            t_new = sorted(t_after - cur_static)
            t_credit = len(cur_static - t_after) + (1 if has_critic_blockers else 0)
            if not t_new or len(t_new) < t_credit:
                cur_plan, cur_ifaces, cur_code, cur_instr, cur_static = t_plan, t_ifaces, t_code, t_instr, t_after
                partial_changed.extend(t_changed)
            else:
                rejected_notes.extend(t_new)

    for rel, source in _plan_interfaces(patch).items():
        if cur_ifaces.get(rel) == source:
            continue
        t_plan, t_changed = _apply_patch(cur_plan, cur_ifaces, {"interfaces": {rel: source}})
        if not t_changed:
            continue
        t_ifaces = _plan_interfaces(t_plan)
        t_code, t_instr = _static_blockers(t_plan, t_ifaces)
        t_after = set(t_code + t_instr)
        t_new = sorted(t_after - cur_static)
        t_credit = len(cur_static - t_after) + (1 if has_critic_blockers else 0)
        if not t_new or len(t_new) < t_credit:
            cur_plan, cur_ifaces, cur_code, cur_instr, cur_static = t_plan, t_ifaces, t_code, t_instr, t_after
            partial_changed.append(rel)
        else:
            rejected_notes.append(f"{rel}: {'; '.join(t_new)}")

    if partial_changed:
        return (
            cur_plan, cur_ifaces, cur_code, cur_instr, True,
            partial_changed, sorted(before - cur_static), sorted(cur_static - before), rejected_notes,
        )
    return plan_out, interfaces, [], [], False, [], [], new, rejected_notes or new


class PlanSpecMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

    @property
    def hypergraph_path(self) -> Path:
        return self.state_dir / "hypergraph.json"

    def _validated_plan(
        self, plan_out: dict[str, Any], plan_payload: dict[str, Any], planner_md: Path
    ) -> tuple[dict[str, Any], dict[str, str], list[str]]:
        """(plan, its interfaces, blockers). Two severity levels:
        - `blockers`: `blocker_code` (stub/import/entrypoint errors) + `blocker_instruction` (task vs interface
          mismatches) + `blocker_critic` (proven critic blockers).
        - `warnings`: non-blocking critic suggestions (and unproven critic blockers).
        Only `blockers` stop the run; when `blockers` is empty, the plan passes immediately."""
        interfaces = _plan_interfaces(plan_out)
        blocker_code, blocker_instruction = _static_blockers(plan_out, interfaces)
        review: tuple[list[str], list[str]] | None = None
        rejected_patch: list[str] = []
        code_budget = CODE_PATCH_BUDGET
        critic_budget = CRITIC_PATCH_BUDGET
        no_progress = 0
        prev_blockers_count: int | None = None
        prev_in_static = False

        for attempt in range(MAX_PLANNER_PATCHES + 1):
            if review is None:
                review = ([], []) if blocker_code else self._plan_review(plan_out, interfaces, plan_payload)
            blocker_critic, warnings = review
            static_blockers = blocker_code + blocker_instruction
            blockers = static_blockers + blocker_critic
            self.logger.log_event(
                "PLAN_CHECKED", attempt=attempt, modules=sorted(interfaces),
                blockers={"code": blocker_code, "instruction": blocker_instruction, "critic": blocker_critic},
                warnings=warnings,
            )
            if not blockers:
                return plan_out, interfaces, []

            if prev_blockers_count is not None:
                transitioned_to_critic = prev_in_static and not static_blockers
                made_progress = transitioned_to_critic or len(blockers) < prev_blockers_count
                no_progress = 0 if made_progress else no_progress + 1

            in_static_phase = bool(static_blockers)
            phase_budget = code_budget if in_static_phase else critic_budget
            if attempt >= MAX_PLANNER_PATCHES or phase_budget <= 0 or no_progress >= NO_PROGRESS_LIMIT:
                return plan_out, interfaces, blockers

            prev_blockers_count = len(blockers)
            prev_in_static = in_static_phase

            self.logger.log_step(
                "PLANNER_SPEC_FEEDBACK",
                f"Plan ma {len(blockers)} blokad i {len(warnings)} ostrzeżeń -> łatka planisty {attempt + 1}/{MAX_PLANNER_PATCHES}",
                {"blockers": blockers, "warnings": warnings, "previous_patch_rejected": rejected_patch},
            )
            retry = self._call_agent(
                planner_md,
                {**plan_payload, "current_plan": _plan_view(plan_out, interfaces),
                 "error_feedback": texts.planner_patch_feedback(blockers, rejected_patch)},
                model_tier="LRM", provider=self.provider,
            )
            if in_static_phase:
                code_budget -= 1
            else:
                critic_budget -= 1

            patch = retry.get("output") if retry.get("status") == "ok" else None
            (
                candidate, c_ifaces, c_code, c_instr, accepted, changed, fixed, new, rejected_notes,
            ) = _apply_patch_with_partial_fallback(
                plan_out, interfaces, patch if isinstance(patch, dict) else {}, static_blockers, bool(blocker_critic),
            )
            before = set(static_blockers)
            after = set(c_code + c_instr) if accepted else before
            self.logger.log_event(
                "PLAN_PATCHED", attempt=attempt, accepted=accepted, changed=changed, fixed=fixed, new=new,
                remaining=sorted(before & after), rejected=rejected_notes,
            )
            if accepted:
                plan_out, interfaces, blocker_code, blocker_instruction, review, rejected_patch = (
                    candidate, c_ifaces, c_code, c_instr, None, rejected_notes,
                )
            else:
                rejected_patch = rejected_notes
        return plan_out, interfaces, []

    def _plan_review(
        self, plan_out: dict[str, Any], interfaces: dict[str, str], plan_payload: dict[str, Any]
    ) -> tuple[list[str], list[str]]:
        """(blocker_critic, warnings) of the plan critic on the whole plan: interfaces, doctests, tasks and blueprint.
        Critic blockers without a valid target in the plan and concrete problem/fix are downgraded to warnings."""
        blueprint = plan_out.get("academic_blueprint") if isinstance(plan_out.get("academic_blueprint"), dict) else {}
        review = self._call_agent(
            self.agents_dir / "planning" / "plan_critic_guard.md",
            {
                "user_prompt": plan_payload.get("user_prompt", ""),
                "tasks": plan_out.get("tasks") or [],
                "interfaces": interfaces,
                "entrypoint": _entrypoint(plan_out),
                "academic_blueprint": {k: v for k, v in blueprint.items() if k not in ("literature_recon", "interfaces")},
                "agent_registry": sorted((read_json_state(self.registry_path).get("agents") or {}).keys()),
            },
            model_tier="LRM", provider=self.provider,
        )
        output = review.get("output") if review.get("status") == "ok" else None
        if not isinstance(output, dict) or output.get("status") not in ("PASS", "FAIL"):
            self.logger.log_event("PLAN_REVIEW_NO_VERDICT", status=review.get("status"), output=str(output)[:300])
            return [], []
        blocker_critic: list[str] = []
        warnings: list[str] = []
        for issue in output.get("issues") or []:
            if isinstance(issue, dict):
                text = texts.critic_finding(str(issue.get("where") or ""), str(issue.get("problem") or ""), str(issue.get("fix") or ""))
                is_blocker = issue.get("blocking") is True and _is_proven_blocker(issue, plan_out, interfaces)
                (blocker_critic if is_blocker else warnings).append(text)
            elif str(issue).strip():
                warnings.append(texts.critic_finding("", str(issue), ""))
        self.logger.log_event(
            "PLAN_REVIEWED", status=output["status"], blocker_critic=blocker_critic, warnings=warnings,
        )
        return blocker_critic, warnings

    def _plan_rejected(self, violations: list[str], tasks: list[dict[str, Any]]) -> dict[str, Any]:
        self.logger.log_step("PLAN_REJECTED", "Plan nadal niewykonalny po poprawkach planisty", {"violations": violations})
        self.logger.log_event("PLAN_REJECTED", violations=violations)
        print(f"  [PLAN ODRZUCONY] {len(violations)} naruszeń specyfikacji:\n    - " + "\n    - ".join(violations), flush=True)
        return {"stop": {"status": "PLAN_REJECTED", "violations": violations, "tasks": tasks, "replan_count": 0}}

    def _build_project_hypergraph(
        self, interfaces: dict[str, str], blueprint: dict[str, Any], tasks: list[dict[str, Any]]
    ) -> Hypergraph:
        """H from the validated plan, saved in state/, and the stubs of σ written to the workspace (no skeleton
        task: a validated specification cannot fail, so nothing can block the entrypoint behind it — X1)."""
        chapters = blueprint.get("planned_chapters") if isinstance(blueprint.get("planned_chapters"), list) else []
        h, problems = build_from_plan(
            interfaces, str(blueprint.get("entrypoint") or ""), tasks, chapters if self.include_docs else [],
            list(blueprint.get("metrics") or []),
        )
        # The bibliography is written by planning (verified arXiv records), not by a task: without this it stayed
        # `spec` for the whole run although every chapter cites it.
        bib = h.vertices.get("references.bib")
        if bib is not None and (self.workspace_dir / "references.bib").is_file():
            bib.state = "verified"
        save(h, self.hypergraph_path)
        self.logger.log_event(
            "H_BUILT", vertices=len(h.vertices), edges=len(h.edges), order=len(h.order), problems=[str(p) for p in problems]
        )
        stubs = [{"filename": rel, "content": stub} for rel, src in interfaces.items() if (stub := stub_source(src))]
        self.logger.log_step("SKELETON_FROM_PLAN", f"Stuby z σ: {len(stubs)} modułów", {"files": [f["filename"] for f in stubs]})
        self._materialize_workspace_artifact(
            stubs[0]["filename"], {"files": stubs, "summary": texts.SKELETON_SUMMARY}, writer={"agent": "harness", "task_id": "H_STUBS"},
        )
        return h
