"""The plan as specification: the critics' verdicts read the same way at every stage, the plan rejected when it
cannot be built, and H with the stubs of σ built from the accepted plan (Audit VI §VII.12.6, A3). The stages that
produce the plan are in `plan_stages` (§XVI)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from adk.core.models import ModelTier
from adk.hypergraph import Hypergraph, build_from_plan, save
from adk.hypergraph.oracles import is_stub
from adk.orchestration import agent_texts as texts
from adk.orchestration.interface_view import interface_view
from adk.tools.verification.contract_check import stub_source


CRITIC_NOTE_CHARS = 1500


def _is_proven_blocker(issue: dict[str, Any], targets: set[str]) -> bool:
    """A critic blocker must name an existing target of what it reviews (`where`), a concrete failure (`problem`),
    and a fix; never about what an example returns, which the harness checks on the code (§XIV Q1)."""
    where = str(issue.get("where") or "").strip().lower()
    if not (where and str(issue.get("problem") or "").strip() and str(issue.get("fix") or "").strip()):
        return False
    if issue.get("blocking") is not True or str(issue.get("category") or "").lower() == "doctest":
        return False
    return any(t.lower() in where for t in targets)


def _affects(issue: dict[str, Any]) -> list[str]:
    """The critic's `affects` (other places its fix changes) as `[where] change` lines; items may be dicts or text."""
    raw = issue.get("affects")
    lines: list[str] = []
    for item in raw if isinstance(raw, list) else []:
        if isinstance(item, dict):
            where, change = str(item.get("where") or "").strip(), str(item.get("change") or "").strip()
            if change:
                lines.append(f"[{where}] {change}" if where else change)
        elif str(item).strip():
            lines.append(str(item).strip())
    return lines


def plan_targets(modules: list[str] | set[str]) -> set[str]:
    """What a finding about the plan may name: a module (path or file name) or a field of the outline."""
    return {*modules, *(Path(rel).name for rel in modules), "academic_blueprint", "entrypoint", "plots", "modules", "metrics", "planned_chapters"}


class PlanSpecMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

    def _call_planning_agent(self, md: Path, payload: dict[str, Any], *, model_tier: ModelTier = "LRM") -> dict[str, Any]:
        """One call of planning, on the large model unless the caller says otherwise (`select_planning_tier`). A failed
        call (`status` error: timeout, unreachable model) is a failed round, not the end of the run: `call_agent` returns
        it as an answer."""
        return self._call_agent(md, payload, model_tier=model_tier, provider=self.provider)

    @property
    def hypergraph_path(self) -> Path:
        return self.state_dir / "hypergraph.json"

    def _critic_review(self, md_name: str, payload: dict[str, Any], targets: set[str]) -> tuple[list[str], list[str]] | None:
        """(blockers, warnings) of one critic, or None when it gave no readable verdict (logged; blocks nothing).
        A blocker without a valid target, a concrete problem and a fix is a warning."""
        review = self._call_planning_agent(self.agents_dir / "planning" / md_name, payload)
        output = review.get("output") if review.get("status") == "ok" else None
        if not isinstance(output, dict) or output.get("status") not in ("PASS", "FAIL"):
            self.logger.log_event("PLAN_REVIEW_NO_VERDICT", critic=Path(md_name).stem, status=review.get("status"), output=str(output)[:300])
            return None
        blockers: list[str] = []
        warnings: list[str] = []
        for issue in output.get("issues") or []:
            if isinstance(issue, dict):
                text = texts.critic_finding(
                    str(issue.get("where") or ""), str(issue.get("problem") or ""), str(issue.get("fix") or ""), _affects(issue),
                )[:CRITIC_NOTE_CHARS]  # one rambling note was 11k characters of the author's next payload (§XXXVIII.1)
                (blockers if _is_proven_blocker(issue, targets) else warnings).append(text)
            elif str(issue).strip():
                warnings.append(texts.critic_finding("", str(issue), ""))
        return blockers, warnings

    def _plan_review(
        self, plan_out: dict[str, Any], interfaces: dict[str, str], plan_payload: dict[str, Any],
        history: list[dict[str, Any]] | None = None,
    ) -> tuple[list[str], list[str]]:
        """(blockers, warnings) of the main critic on the fused plan: outline and every interface together. Its
        blockers name a module (that module is redesigned) or an outline field (the outline is revised)."""
        verdict = self._critic_review("plan_critic_guard.md", {
            "user_prompt": plan_payload.get("user_prompt", ""),
            "outline": plan_out.get("outline") or {},
            "interfaces": {rel: interface_view(src) for rel, src in interfaces.items()},
            "review_history": history or [],
            "available_packages": plan_payload.get("available_packages"),
            "experiment_time_limit_s": plan_payload.get("experiment_time_limit_s"),
            "existing_files": plan_payload.get("existing_files") or {},
        }, plan_targets(interfaces))
        blockers, warnings = verdict or ([], [])
        self.logger.log_event("PLAN_REVIEWED", status="FAIL" if blockers else "PASS", blocker_critic=blockers, warnings=warnings)
        return blockers, warnings

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
            list(blueprint.get("metrics") or []), str(blueprint.get("plots") or ""),
        )
        # The bibliography is written by planning (verified arXiv records), not by a task: without this it stayed
        # `spec` for the whole run although every chapter cites it.
        bib = h.vertices.get("references.bib")
        if bib is not None and (self.workspace_dir / "references.bib").is_file():
            bib.state = "verified"
        # Code the workspace already had (a brownfield project) is kept, never replaced by its stub (2026-11-20, 03:
        # declaring the existing baseline would have erased it). Nothing re-verifies it unless a task targets it.
        targeted = {str(t.get("target_node", "")).replace("\\", "/") for t in tasks if isinstance(t, dict)}
        existing = {rel for rel in interfaces if rel in h.vertices and (self.workspace_dir / rel).is_file()
                    and not is_stub((self.workspace_dir / rel).read_text(encoding="utf-8", errors="replace"))}
        for rel in existing:
            h.vertices[rel].state = "impl" if rel in targeted else "verified"
        save(h, self.hypergraph_path)
        self.logger.log_event(
            "H_BUILT", vertices=len(h.vertices), edges=len(h.edges), order=len(h.order), problems=[str(p) for p in problems]
        )
        stubs = [{"filename": r, "content": s} for r, src in interfaces.items() if r not in existing and (s := stub_source(src))]
        if not stubs:
            return h
        self.logger.log_step("SKELETON_FROM_PLAN", f"Stuby z σ: {len(stubs)} modułów", {"files": [f["filename"] for f in stubs]})
        self._materialize_workspace_artifact(
            stubs[0]["filename"], {"files": stubs, "summary": texts.SKELETON_SUMMARY}, writer={"agent": "harness", "task_id": "H_STUBS"},
        )
        return h
