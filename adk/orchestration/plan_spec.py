"""The plan as specification: validate the code part of the plan before any code exists, then build H and write
the stubs of σ (Audit VI §VII.12.6, A3). Replaces the single interface retry and the SKELETON task."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from adk.hypergraph import Hypergraph, build_from_plan, code_violations, save
from adk.orchestration import agent_texts as texts
from adk.orchestration.plan_interfaces import _interface_gaps, _plan_interfaces
from adk.tools.verification.contract_check import stub_source

PLANNER_SPEC_RETRIES = 2  # O1 (2026-11-16): two corrections by the planner, then the run stops with the list


def _entrypoint(plan_out: dict[str, Any]) -> str:
    blueprint = plan_out.get("academic_blueprint") if isinstance(plan_out.get("academic_blueprint"), dict) else {}
    return str(blueprint.get("entrypoint") or plan_out.get("entrypoint") or "").strip()


class PlanSpecMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

    @property
    def hypergraph_path(self) -> Path:
        return self.state_dir / "hypergraph.json"

    def _validated_plan(
        self, plan_out: dict[str, Any], plan_payload: dict[str, Any], planner_md: Path
    ) -> tuple[dict[str, Any], dict[str, str], list[str]]:
        """(plan, its interfaces, problems still making the plan unexecutable). Gaps between task prose and
        interfaces go back to the planner too, but only a plan without tasks, without interfaces or with an
        unexecutable specification is fatal: every run is built on σ, there is no unspecified path."""
        interfaces = _plan_interfaces(plan_out)
        for attempt in range(PLANNER_SPEC_RETRIES + 1):
            if interfaces:
                fatal = [str(v) for v in code_violations(interfaces, _entrypoint(plan_out))[1]]
            else:
                fatal = [texts.PLAN_WITHOUT_INTERFACES]
            if not plan_out.get("tasks"):
                fatal.append(texts.PLAN_WITHOUT_TASKS)
            gaps = _interface_gaps(plan_out.get("tasks") or [], interfaces)
            problems = fatal + gaps
            self.logger.log_event("PLAN_CHECKED", attempt=attempt, modules=sorted(interfaces), violations=fatal, gaps=gaps)
            if not problems or attempt == PLANNER_SPEC_RETRIES:
                return plan_out, interfaces, fatal
            self.logger.log_step(
                "PLANNER_SPEC_FEEDBACK",
                f"Plan nie spełnia specyfikacji ({len(problems)} naruszeń) -> poprawka planisty {attempt + 1}/{PLANNER_SPEC_RETRIES}",
                {"problems": problems},
            )
            retry = self._call_agent(
                planner_md, {**plan_payload, "error_feedback": texts.planner_spec_feedback(problems)},
                model_tier="LRM", provider=self.provider,
            )
            candidate = retry.get("output") if retry.get("status") == "ok" else None
            candidate = candidate if isinstance(candidate, dict) else {}
            candidate_interfaces = _plan_interfaces(candidate)
            # A correction that drops the tasks or the interfaces is no correction.
            if isinstance(candidate.get("tasks"), list) and candidate["tasks"] and candidate_interfaces:
                plan_out, interfaces = candidate, candidate_interfaces
        return plan_out, interfaces, []

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
