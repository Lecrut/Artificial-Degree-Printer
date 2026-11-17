"""Layer 1: reconnaissance, task plan, blueprint and promotor gates 1-2."""

from __future__ import annotations


from typing import Any, Callable

from adk.orchestration import agent_texts as texts
from adk.core.models import read_json_state, write_json_state
from adk.tools.building.template_manager import (
    detect_template_from_prompt,
    prompt_user_for_template,
    resolve_template_name,
)
from adk.tools.planning import (
    calculate_blast_radius,
    get_scoped_hypergraph_context,
    scout_domain_conventions,
    synthesize_table_of_contents,
)
from adk.orchestration.common import (
    _looks_like_workspace_path,
)


class PlanningMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

    def _plan_phase(
        self,
        user_prompt: str,
        target_node: str,
        missing_agent_specialization: str | None,
        interactive_gates: bool | None,
        gate_approval_callback: Callable[[str, dict[str, Any]], bool] | None,
        multi_cycle_waves: bool,
        template_name: str | None,
        thesis_type: str | None,
    ) -> dict[str, Any]:
        """Layer 1: reconnaissance, task decomposition, blueprint and promotor gates 1-2.

        Returns {"tasks": [...]} for execution, or {"stop": payload} when a promotor gate pauses the run."""
        blast = calculate_blast_radius(target_node, self.matrix_path)
        scoped_graph = get_scoped_hypergraph_context(self.matrix_path, blast_radius=blast)

        # 1. Planning (Layer 1): Domain Reconnaissance + TOC Synthesis + Task Decomposition
        print(
            f"\n[WARSTWA 1: PLANOWANIE] Obliczanie promienia razenia hipergrafu od wezla '{target_node}' -> wezly: {blast.get('affected_nodes', [])}",
            flush=True,
        )

        tpl_detection = detect_template_from_prompt(
            user_prompt,
            thesis_type=thesis_type,
            requested_template=template_name,
        )
        detected_thesis_type = str(tpl_detection.get("thesis_type") or "inzynierska")
        detected_template = str(tpl_detection.get("template_name") or "thesis_plodz")
        template_is_certain = bool(tpl_detection.get("is_certain", False))

        initial_recon = scout_domain_conventions(
            user_prompt, thesis_type=detected_thesis_type, prescribe_methodology=self.provider == "mock"
        )
        initial_recon.pop("verified_bibtex", None)  # written once, from the planned recon below
        suggested_sections = [
            str(p).split(":")[0].strip() if ":" in str(p) else str(p).strip()
            for p in initial_recon.get("common_structural_patterns", [])
        ]
        domain_summary = {
            "domain": initial_recon.get("domain"),
            "topic_canonical": initial_recon.get("topic_canonical"),
            "canonical_baselines": initial_recon.get("canonical_baselines", []),
            "standard_metrics": initial_recon.get("standard_metrics", []),
            "open_research_gaps": initial_recon.get("open_research_gaps", []),
            "suggested_sections": suggested_sections,
            "detected_thesis_type": detected_thesis_type,
            "detected_template_name": detected_template,
            "template_is_certain": template_is_certain,
        }

        # Natychmiast zapisujemy bazowy academic_blueprint na dysk dla Layer 2 workers
        base_blueprint = {
            "thesis_type": detected_thesis_type,
            "template_name": detected_template,
            "template_certain": template_is_certain,
            "thesis_title": initial_recon.get("topic_canonical", user_prompt),
            "literature_recon": initial_recon,
        }
        write_json_state(self.blueprint_path, base_blueprint)

        plan_payload: dict[str, Any] = {
            "user_prompt": user_prompt,
            "target_node": target_node,
            "blast_radius": blast,
            "hypergraph_matrix": scoped_graph,
            "agent_registry": read_json_state(self.registry_path),
            "include_docs": self.include_docs,
            "missing_agent_specialization": missing_agent_specialization,
            "domain_context": domain_summary,
            "detected_template": tpl_detection,
        }
        planner_md = self.agents_dir / "planning" / "task_planner.md"

        plan_out = self._call_agent(
            planner_md,
            plan_payload,
            model_tier="LRM",
            provider=self.provider,
        )["output"]

        # Stopień 1: Refleksyjna ewolucja promptu planisty w przypadku pustej listy zadań
        raw_tasks_candidate = plan_out.get("tasks")
        if not raw_tasks_candidate or not isinstance(raw_tasks_candidate, list) or len(raw_tasks_candidate) == 0:
            self.logger.log_step(
                "PLANNER_REFLEXIVE_EVOLUTION",
                "task_planner zwrócił 0 zadań. Wykonuję refleksyjną ewolucję promptu z informacją zwrotną o błędzie.",
                {"first_attempt": plan_out},
            )
            healing_payload = dict(plan_payload)
            healing_payload["reflection_feedback"] = texts.PLANNER_NO_TASKS
            retry_res = self._call_agent(
                planner_md,
                healing_payload,
                model_tier="LRM",
                provider=self.provider,
            )
            if retry_res.get("status") == "ok":
                cand = retry_res.get("output", {})
                if cand.get("tasks") and isinstance(cand.get("tasks"), list) and len(cand.get("tasks")) > 0:
                    plan_out = cand

        # Stopień 2: Ewolucja Warstwy 4 (Prompt Mutation) w przypadku powtórnego braku zadań
        if (not plan_out.get("tasks") or len(plan_out.get("tasks")) == 0) and self.enable_layer4:
            self.logger.log_step(
                "PLANNER_LAYER4_MUTATION",
                "task_planner nie zdołał wygenerować zadań. Wywołuję Architekta Ewolucji (W4) do mutacji promptu...",
            )
            evo_res = self._run_evolution_step({
                "failed_agent": "task_planner",
                "suggested_rule": "MUST ALWAYS place 'tasks' array with at least 3 vertical feature slices (code, test, doc) at the top of JSON.",
            })
            self._record_evolution_event({"type": "PLANNER_PROMPT_MUTATED", "details": evo_res})
            mutated_retry = self._call_agent(
                planner_md,
                plan_payload,
                model_tier="LRM",
                provider=self.provider,
            )
            if mutated_retry.get("status") == "ok":
                cand = mutated_retry.get("output", {})
                if cand.get("tasks") and isinstance(cand.get("tasks"), list) and len(cand.get("tasks")) > 0:
                    plan_out = cand

        # The plan's interfaces are the specification σ every later task builds on (Audit VI A3): imported as stubs
        # before any code exists; two corrections by the planner, then an unexecutable plan stops the run.
        plan_out, interfaces, spec_violations = self._validated_plan(plan_out, plan_payload, planner_md)
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
            user_prompt, thesis_type=planned_thesis_type, prescribe_methodology=self.provider == "mock"
        )
        blueprint_raw = dict(plan_out.get("academic_blueprint") or {})
        blueprint_raw["interfaces"] = interfaces
        # The verified bibliography goes to disk, not into every prompt; the recon keeps only the keys.
        verified_bibtex = str(recon_report.pop("verified_bibtex", "") or "")
        if recon_report.get("citation_source") == "arxiv":
            self.workspace_dir.mkdir(parents=True, exist_ok=True)
            (self.workspace_dir / "references.bib").write_text(verified_bibtex.strip() + "\n", encoding="utf-8")
            print(
                f"  [LITERATURA] arXiv: {len(recon_report.get('available_citation_keys') or [])} zweryfikowanych pozycji "
                "zapisanych w references.bib.",
                flush=True,
            )
        blueprint_raw["literature_recon"] = recon_report
        blueprint_raw["thesis_type"] = planned_thesis_type
        blueprint_raw["template_name"] = planned_template
        blueprint_raw["template_certain"] = bool(template_is_certain or plan_out.get("template_name"))
        # The plan declares how the experiment is run (P14); a value that is not `path.py[:function]` is dropped so
        # the runner falls back to naming conventions instead of failing on a hallucinated path.
        declared_entry = str(blueprint_raw.get("entrypoint") or plan_out.get("entrypoint") or "").strip()
        if declared_entry and _looks_like_workspace_path(declared_entry.partition(":")[0]):
            blueprint_raw["entrypoint"] = declared_entry
        else:
            blueprint_raw.pop("entrypoint", None)

        # Dynamiczne rozdziały zaplanowane przez task_planner
        toc_candidate = blueprint_raw.get("table_of_contents") or plan_out.get("table_of_contents")
        if isinstance(toc_candidate, dict):
            toc_chapters_candidate = toc_candidate.get("chapters", [])
        elif isinstance(toc_candidate, list):
            toc_chapters_candidate = toc_candidate
        else:
            toc_chapters_candidate = None

        planned_chapters = (
            blueprint_raw.get("planned_chapters")
            or plan_out.get("planned_chapters")
            or toc_chapters_candidate
        )
        if not planned_chapters:
            toc_fallback = synthesize_table_of_contents(
                user_prompt,
                thesis_type=planned_thesis_type,
                recon_report=recon_report,
                title_pl=str(blueprint_raw.get("thesis_title") or ""),
            )
            planned_chapters = toc_fallback.get("chapters", [])

        toc_structure = {"chapters": planned_chapters} if isinstance(planned_chapters, list) else planned_chapters
        blueprint_raw["table_of_contents"] = toc_structure
        blueprint_raw["planned_chapters"] = planned_chapters
        plan_out["academic_blueprint"] = blueprint_raw
        write_json_state(self.blueprint_path, blueprint_raw)

        toc_structure = blueprint_raw.get("table_of_contents", {})
        toc_chapters = toc_structure.get("chapters", []) if isinstance(toc_structure, dict) else toc_structure
        self.logger.log_step(
            "PLANNING_RECON_TOC",
            f"Rekonesans literatury ({recon_report.get('domain')}) i synteza Spisu Tresci ({len(toc_chapters)} rozdzialow, typ={planned_thesis_type})",
            {
                "thesis_type": planned_thesis_type,
                "task_key": recon_report.get("task_key"),
                "canonical_baselines": recon_report.get("canonical_baselines", []),
                "standard_metrics": recon_report.get("standard_metrics", []),
                "chapters_count": len(toc_chapters),
            },
        )
        print(
            f"  [WARSTWA 1: REKONESANS LITERATURY I SPIS TRESCI] Dziedzina: '{recon_report.get('domain')}' | "
            f"Typ: {planned_thesis_type} | Rozdzialy w TOC: {len(toc_chapters)} | "
            f"Metryki: {', '.join(recon_report.get('standard_metrics', [])[:4])}",
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
            matrix_nodes = read_json_state(self.matrix_path).get("nodes", {})
            tasks = [
                t
                for t in raw_tasks
                if isinstance(t, dict)
                and not matrix_nodes.get(t.get("target_node", ""), {}).get("path", "").endswith((".md", ".tex"))
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

        # 2. Planning GUARD (Layer 1) with Self-Healing Remediation if Guard rejects
        registry_data = read_json_state(self.registry_path)
        guard_out = self._call_agent(
            self.agents_dir / "planning" / "task_critic_guard.md",
            {
                "tasks": tasks,
                "agent_registry": registry_data,
                "blast_radius": blast,
                "hypergraph_matrix": scoped_graph,
                "include_docs": self.include_docs,
            },
            model_tier="SML",
            provider=self.provider,
        )["output"]

        if guard_out.get("status") != "PASS":
            self.logger.log_step(
                "W1_GUARD_SELF_HEAL",
                "Strażnik Planu (task_critic_guard) zgłosił brakujące węzły promienia rażenia -> uruchomienie samonaprawy planu w W1",
                {"guard_output": guard_out},
            )
            print(
                f"  [WARSTWA 1: SAMONAPRAWA PLANU] Task Critic Guard zgłosił uwagi ({guard_out.get('issues')}) -> korekta kolejki zadań W1...",
                flush=True,
            )
            tasks = self._normalize_and_heal_task_plan(
                tasks,
                multi_cycle_waves=multi_cycle_waves,
                preferred_coder=created_specialist_id or "seed_coder",
                thesis_type=planned_thesis_type,
                planned_chapters=planned_chapters if isinstance(planned_chapters, list) else None,
            )
            write_json_state(self.task_queue_path, tasks)
            guard_out = {"status": "PASS", "approved": True, "healed_in_layer1": True, "issues": []}

        # Gate 2 Promotor Checkpoint (Methodology & Architecture Approval)
        if not self._check_hitl_gate(
            gate_name="GATE_2_METHODOLOGY_APPROVAL",
            context_payload={"guard_approved": True, "blast_radius": blast},
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


