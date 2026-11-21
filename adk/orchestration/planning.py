"""Layer 1: reconnaissance, task plan, blueprint and promotor gates 1-2."""

from __future__ import annotations


from pathlib import Path
from typing import Any, Callable

from adk.core.models import read_json_state, write_json_state
from adk.tools.building.template_manager import (
    detect_template_from_prompt,
    prompt_user_for_template,
    resolve_template_name,
)
from adk.tools.building.experiment_runner import EXPERIMENT_TIMEOUT_S
from adk.tools.planning import scout_domain_conventions
from adk.orchestration.common import (
    _looks_like_workspace_path,
    available_package_imports,
)

EXISTING_FILE_CHARS = 8000  # per file: a brownfield module is shown whole, a generated monster is cut


def _existing_code(workspace: Path, limit: int | None = EXISTING_FILE_CHARS) -> dict[str, str]:
    """Python files the workspace already has before planning (a brownfield project), by relative path."""
    found: dict[str, str] = {}
    for path in sorted(workspace.rglob("*.py")) if workspace.is_dir() else []:
        rel = path.relative_to(workspace)
        if {"logs", "__pycache__", "figures"} & set(rel.parts):
            continue
        found[rel.as_posix()] = path.read_text(encoding="utf-8", errors="replace")[:limit]
    return found


class PlanningMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

    def _plan_phase(
        self,
        user_prompt: str,
        missing_agent_specialization: str | None,
        interactive_gates: bool | None,
        gate_approval_callback: Callable[[str, dict[str, Any]], bool] | None,
        multi_cycle_waves: bool,
        template_name: str | None,
        thesis_type: str | None,
    ) -> dict[str, Any]:
        """Layer 1: reconnaissance, task decomposition, blueprint and promotor gates 1-2.

        Returns {"tasks": [...]} for execution, or {"stop": payload} when a promotor gate pauses the run."""
        # 1. Planning (Layer 1): Domain Reconnaissance + TOC Synthesis + Task Decomposition. The plan creates the
        # hypergraph; before it there is none to scope (the old matrix gave the planner an empty seed and 'v1').
        print("\n[WARSTWA 1: PLANOWANIE]", flush=True)

        tpl_detection = detect_template_from_prompt(
            user_prompt,
            thesis_type=thesis_type,
            requested_template=template_name,
        )
        detected_thesis_type = str(tpl_detection.get("thesis_type") or "inzynierska")
        detected_template = str(tpl_detection.get("template_name") or "thesis_plodz")
        template_is_certain = bool(tpl_detection.get("is_certain", False))

        initial_recon = scout_domain_conventions(
            user_prompt, thesis_type=detected_thesis_type
        )
        initial_recon.pop("verified_bibtex", None)  # written once, from the planned recon below
        # Only what was detected about the request; domain, metrics, baselines and chapters are the plan's (§XIII F3).
        domain_summary = {
            "detected_thesis_type": detected_thesis_type,
            "detected_template_name": detected_template,
            "template_is_certain": template_is_certain,
        }

        # Natychmiast zapisujemy bazowy academic_blueprint na dysk dla Layer 2 workers
        base_blueprint = {
            "thesis_type": detected_thesis_type,
            "template_name": detected_template,
            "template_certain": template_is_certain,
            "thesis_title": user_prompt,
            "literature_recon": initial_recon,
        }
        write_json_state(self.blueprint_path, base_blueprint)

        plan_payload: dict[str, Any] = {
            "user_prompt": user_prompt,
            "agent_registry": read_json_state(self.registry_path),
            "include_docs": self.include_docs,
            "missing_agent_specialization": missing_agent_specialization,
            "domain_context": domain_summary,
            "detected_template": tpl_detection,
            # What the planner cannot see otherwise (2026-11-20: 04 planned on torch, 03 never saw its baseline).
            "available_packages": sorted(available_package_imports().values()),
            "existing_files": _existing_code(self.workspace_dir),
            "experiment_time_limit_s": EXPERIMENT_TIMEOUT_S,
        }
        # Planning in stages (§XVI): outline, then each module's interface, then the tasks, then the whole plan under
        # the main critic. A finding reopens only the part it is about; an unexecutable plan stops the run.
        plan_out, interfaces, spec_violations = self._staged_plan(plan_payload)
        if spec_violations:
            return self._plan_rejected(spec_violations, plan_out.get("tasks") or [])

        planned_thesis_type = str(
            (detected_thesis_type if template_is_certain else None)
            or plan_out.get("thesis_type")
            or detected_thesis_type
        )
        self.planned_thesis_type = planned_thesis_type
        planned_template = resolve_template_name(
            thesis_type=planned_thesis_type,
            requested_template=(
                (detected_template if template_is_certain else None)
                or plan_out.get("template_name")
            ),
        )
        self.planned_template = planned_template
        if not template_is_certain and not plan_out.get("template_name"):
            tpl_question = str(tpl_detection.get("question") or "Którego szablonu użyć: 'thesis_plodz' czy 'paper_ieee'?")
            self.logger.log_step(
                "TEMPLATE_UNCERTAIN_HITL",
                f"Brak jednoznacznego określenia szablonu w zapytaniu -> zapytanie użytkownika: {tpl_question}",
                {"detected_template": tpl_detection},
            )
            if gate_approval_callback is None and self.gate_approval_callback is None:
                planned_template, planned_thesis_type = prompt_user_for_template(
                    default_template=planned_template,
                    default_thesis_type=planned_thesis_type,
                )

        recon_report = scout_domain_conventions(
            user_prompt, thesis_type=planned_thesis_type
        )
        blueprint_raw = dict(plan_out.get("academic_blueprint") or {})
        blueprint_raw["interfaces"] = interfaces
        # The verified bibliography goes to disk, not into every prompt; the recon keeps only the keys.
        verified_bibtex = str(recon_report.pop("verified_bibtex", "") or "")
        if verified_bibtex.strip():
            self.workspace_dir.mkdir(parents=True, exist_ok=True)
            (self.workspace_dir / "references.bib").write_text(verified_bibtex.strip() + "\n", encoding="utf-8")
            print(
                f"  [LITERATURA] {recon_report.get('citation_source')}: {len(recon_report.get('available_citation_keys') or [])} zweryfikowanych pozycji "
                "zapisanych w references.bib.",
                flush=True,
            )
        blueprint_raw["literature_recon"] = recon_report
        blueprint_raw["thesis_type"] = planned_thesis_type
        blueprint_raw["template_name"] = planned_template
        blueprint_raw["template_certain"] = bool(template_is_certain or plan_out.get("template_name"))
        # The plan declares how the experiment is run (P14); a value that is not `path.py[:function]` is dropped
        # (plan validation already required a planned entrypoint; nothing is guessed by file name, §XIII F5).
        declared_entry = str(blueprint_raw.get("entrypoint") or plan_out.get("entrypoint") or "").strip()
        if declared_entry and _looks_like_workspace_path(declared_entry.partition(":")[0]):
            blueprint_raw["entrypoint"] = declared_entry
        else:
            blueprint_raw.pop("entrypoint", None)
        declared_plots = str(blueprint_raw.get("plots") or plan_out.get("plots") or "").strip()
        if declared_plots:
            blueprint_raw["plots"] = declared_plots

        # Dynamiczne rozdziały zaplanowane przez task_planner
        toc_candidate = blueprint_raw.get("table_of_contents") or plan_out.get("table_of_contents")
        if isinstance(toc_candidate, dict):
            toc_chapters_candidate = toc_candidate.get("chapters", [])
        elif isinstance(toc_candidate, list):
            toc_chapters_candidate = toc_candidate
        else:
            toc_chapters_candidate = None

        # No fallback table of contents: a plan without chapters does not pass validation (§XIII F4).
        planned_chapters = (
            blueprint_raw.get("planned_chapters")
            or plan_out.get("planned_chapters")
            or toc_chapters_candidate
            or []
        )

        toc_structure = {"chapters": planned_chapters} if isinstance(planned_chapters, list) else planned_chapters
        blueprint_raw["table_of_contents"] = toc_structure
        blueprint_raw["planned_chapters"] = planned_chapters
        plan_out["academic_blueprint"] = blueprint_raw
        write_json_state(self.blueprint_path, blueprint_raw)

        toc_structure = blueprint_raw.get("table_of_contents", {})
        toc_chapters = toc_structure.get("chapters", []) if isinstance(toc_structure, dict) else toc_structure
        self.logger.log_step(
            "PLANNING_RECON_TOC",
            f"Rekonesans literatury ({len(recon_report.get('available_citation_keys') or [])} pozycji) i spis tresci planu ({len(toc_chapters)} rozdzialow, typ={planned_thesis_type})",
            {
                "thesis_type": planned_thesis_type,
                "citations": len(recon_report.get("available_citation_keys") or []),
                "chapters_count": len(toc_chapters),
            },
        )
        print(
            f"  [WARSTWA 1: REKONESANS LITERATURY I SPIS TRESCI] Typ: {planned_thesis_type} | "
            f"Rozdzialy w planie: {len(toc_chapters)} | Metryki planu: {', '.join(blueprint_raw.get('metrics') or [])}",
            flush=True,
        )

        raw_tasks: list[dict[str, Any]] = plan_out.get("tasks", [])
        created_specialist_id: str | None = None
        missing_spec_to_create = plan_out.get("missing_agent_specialization") or missing_agent_specialization
        if missing_spec_to_create and self.enable_layer4:
            missing_spec = str(missing_spec_to_create)
            print(
                f"  [WARSTWA 1 -> WARSTWA 4: KREACJA AGENTA] Brak specjalizacji '{missing_spec}' -> tworzenie nowego agenta...",
                flush=True,
            )
            evo_create = self._run_evolution_step(
                {"missing_specialization": missing_spec},
                tasks_in_memory=raw_tasks,
            )
            created_specialist_id = evo_create.get("details", {}).get("agent_id")
            if created_specialist_id:
                for t in raw_tasks:
                    if isinstance(t, dict) and t.get("assigned_agent") in (missing_spec, "missing", None):
                        t["assigned_agent"] = created_specialist_id

        if not self.include_docs:
            tasks = [
                t
                for t in raw_tasks
                if isinstance(t, dict)
                and not str(t.get("target_node", "")).partition("#")[0].endswith((".md", ".tex"))
                and t.get("assigned_agent") not in ("seed_writer", "sota_researcher", "background_researcher", "discoverer_researcher")
            ]
        else:
            tasks = [t for t in raw_tasks if isinstance(t, dict)]

        if multi_cycle_waves:
            tasks = self._normalize_and_heal_task_plan(
                tasks,
                multi_cycle_waves=True,
                preferred_coder=created_specialist_id or "seed_coder",
                thesis_type=planned_thesis_type,
                planned_chapters=planned_chapters if isinstance(planned_chapters, list) else None,
            )

        # The stubs come from the validated specification (plan_spec); a planned skeleton task is redundant.
        tasks = [t for t in tasks if str(t.get("task_id", "")).upper() != "SKELETON"]
        write_json_state(self.task_queue_path, tasks)
        self.hypergraph = self._build_project_hypergraph(interfaces, blueprint_raw, tasks)

        # Gate 1 Promotor Checkpoint (Scope & Thesis Statement Approval)
        gate1_name = str(plan_out.get("hitl_gate") or "GATE_1_OUTLINE_APPROVAL")
        if not self._check_hitl_gate(
            gate_name=gate1_name,
            context_payload={"tasks_count": len(tasks), "academic_blueprint": plan_out.get("academic_blueprint")},
            interactive_gates=interactive_gates,
            gate_approval_callback=gate_approval_callback,
        ):
            return {"stop": {
                "status": "HITL_PAUSED",
                "gate": gate1_name,
                "hitl": read_json_state(self.hitl_flag_path),
                "tasks": tasks,
                "replan_count": 0,
            }}

        # The critics already judged this plan stage by stage (`plan_stages`), before H and the stubs existed.
        # Gate 2 Promotor Checkpoint (Methodology & Architecture Approval)
        if not self._check_hitl_gate(
            gate_name="GATE_2_METHODOLOGY_APPROVAL",
            context_payload={"interfaces": sorted(interfaces), "entrypoint": blueprint_raw.get("entrypoint")},
            interactive_gates=interactive_gates,
            gate_approval_callback=gate_approval_callback,
        ):
            return {"stop": {
                "status": "HITL_PAUSED",
                "gate": "GATE_2_METHODOLOGY_APPROVAL",
                "hitl": read_json_state(self.hitl_flag_path),
                "tasks": tasks,
                "replan_count": 0,
            }}
        return {"tasks": tasks}


