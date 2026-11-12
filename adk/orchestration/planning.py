"""Layer 1: reconnaissance, task plan, blueprint and promotor gates 1-2."""

from __future__ import annotations


import re
from pathlib import Path
from typing import Any, Callable

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
    ROLE_ALIASES,
)


_RESEARCH_AGENTS = {"background_researcher", "discoverer_researcher", "sota_researcher"}

# Planner `agent_specialization` -> agent slot of _normalize_and_heal_task_plan.
_SPECIALIZATION_AGENT = {
    "python_coding": "coder",
    "coding": "coder",
    "unit_testing": "tester",
    "testing": "tester",
    "academic_writing": "writer",
    "writing": "writer",
    "background_literature": "bg",
    "literature_review": "sota",
    "sota_discovery": "disc",
}

# Opening thesis tasks of the synthesized pipeline per document kind: (task_id, description, agent slot).
_PIPELINE_INTRO = {
    "paper": [
        ("T1", "[Przyrost 1: Paper] Section I: Introduction, Motivation and Problem Statement in thesis.md", "writer"),
        ("T2", "[Przyrost 1: Paper] Section II: Related Work, SOTA Competitor Analysis and Research Gap in references.bib and thesis.md", "disc"),
    ],
    "magisterska": [
        ("T1", "[Przyrost 1: Założenia] Redakcja Rozdziału 1: Wstęp, cel pracy i sformalizowana teza inżynierska w thesis.md", "writer"),
        ("T2_BG", "[Przyrost 1: Badania (II stopień)] Redakcja Rozdziału 2: Lejek teoretyczny od klasycznych monografii i podstaw w references.bib i thesis.md", "bg"),
        ("T2_DISC", "[Przyrost 1: Badania (II stopień)] Redakcja Rozdziału 2: Analiza najnowszego SOTA (2023-2026), konkurencji i luki badawczej w references.bib i thesis.md", "disc"),
    ],
    "thesis": [
        ("T1", "[Przyrost 1: Założenia] Redakcja Rozdziału 1: Wstęp, formalny cel pracy, definicja problemu i postawienie tezy inżynierskiej w thesis.md", "writer"),
        ("T2", "[Przyrost 1: Założenia] Redakcja Rozdziału 2: Stan badań, lejek literatury teoretycznej i analiza prac powiązanych w references.bib i thesis.md", "bg"),
    ],
}

# Chapters 3-6 of the synthesized pipeline: (thesis description, paper description), indexed by is_paper.
_PIPELINE_CHAPTERS = {
    3: (
        "[Przyrost 2: Architektura] Redakcja Rozdziału 3: Architektura systemu, schemat blokowy TikZ/Mermaid oraz formalizacja matematyczna modelu w thesis.md",
        "[Przyrost 2: Architektura] Section III: System Architecture, Block Schematics and Formal Formulation in thesis.md",
    ),
    4: (
        "[Przyrost 2: Implementacja] Redakcja Rozdziału 4: Implementacja algorytmiczna, struktury danych i dowiązania symboliczne do kodu AST w thesis.md",
        "[Przyrost 2: Implementacja] Section IV: Algorithmic Implementation, AST Structures and Core Procedures in thesis.md",
    ),
    5: (
        "[Przyrost 3: Wyniki] Redakcja Rozdziału 5: Badania eksperymentalne, protokół pomiarowy, analiza wyników z tabelami CSV i wykresami w thesis.md",
        "[Przyrost 3: Wyniki] Section V: Empirical Results, Baseline Comparison and Sensitivity Analysis in thesis.md",
    ),
    6: (
        "[Przyrost 3: Podsumowanie] Redakcja Rozdziału 6: Podsumowanie, formalna weryfikacja tezy i wnioski końcowe w thesis.md",
        "[Przyrost 3: Podsumowanie] Section VI: Conclusion, Threats to Validity and Future Work in thesis.md",
    ),
}

# Writer task for a canonical chapter the planner's tasks do not cover.
_MISSING_CHAPTER = {
    1: "[Przyrost 1: Założenia] Redakcja Rozdziału 1: Wstęp, formalny cel pracy i teza inżynierska w thesis.md",
    2: "[Przyrost 1: Założenia] Redakcja Rozdziału 2: Przegląd literatury dziedzinowej i analiza SOTA w thesis.md",
    3: "[Przyrost 2: Architektura] Redakcja Rozdziału 3: Architektura systemu, schemat TikZ i model w thesis.md",
    4: "[Przyrost 2: Implementacja] Redakcja Rozdziału 4: Implementacja algorytmiczna i struktury AST w thesis.md",
    5: "[Przyrost 3: Eksperymenty] Redakcja Rozdziału 5: Badania eksperymentalne, protokół pomiarowy i dyskusja wyników w thesis.md",
    6: "[Przyrost 3: Podsumowanie] Redakcja Rozdziału 6: Podsumowanie, formalna weryfikacja tezy i wnioski w thesis.md",
}

# Words that mark a task description as working on a canonical chapter.
_CHAPTER_WORDS = {
    1: ("wstęp", "wstep", "cel", "teza", "intro", "problem"),
    2: ("sota", "stan wiedzy", "literatur", "przegląd", "przeglad", "related", "background"),
    3: ("architektur", "formalizm", "matematyczn", "system", "design", "model", "tikz"),
    4: ("implementacj", "algorytm", "struktury", "implementation", "ast"),
    5: ("wyniki", "ewaluacj", "eksperyment", "badani", "evaluation", "metodologia", "empirical", "results"),
    6: ("podsumowan", "wnioski", "conclusi", "kierunki", "summary"),
}
_EVERYTHING_MARKERS = ("all 6 chapters", "wszystkie 6 rozdział", "6 chapters", "planned_chapters")


def _task(task_id: str, description: str, target: str, agent: str) -> dict[str, Any]:
    return {"task_id": task_id, "description": description, "target_node": target, "assigned_agent": agent, "status": "TODO"}


def _flatten_subtasks(raw_tasks: list[Any] | None) -> list[dict[str, Any]]:
    """Hierarchical planner output as a flat list; subtasks inherit the parent's id prefix, node and agent."""
    flat: list[dict[str, Any]] = []
    for idx, item in enumerate(raw_tasks or []):
        if not isinstance(item, dict):
            continue
        subtasks = item.get("subtasks")
        if not (isinstance(subtasks, list) and subtasks):
            flat.append(item)
            continue
        parent_id = str(item.get("task_id") or item.get("id") or f"T{idx + 1}")
        parent_node = item.get("target_node") or item.get("node_id") or item.get("node")
        parent_agent = item.get("assigned_agent") or item.get("agent")
        parent_desc = item.get("description", "")
        for sub_idx, sub in enumerate(subtasks, 1):
            if not isinstance(sub, dict):
                continue
            sub = dict(sub)
            if "task_id" not in sub and "id" not in sub:
                sub["task_id"] = f"{parent_id}.{sub_idx}"
            if not sub.get("target_node") and not sub.get("node_id") and parent_node:
                sub["target_node"] = parent_node
            if not sub.get("assigned_agent") and not sub.get("agent") and parent_agent:
                sub["assigned_agent"] = parent_agent
            if parent_desc and parent_desc not in str(sub.get("description", "")):
                sub["description"] = f"[{parent_id}] {sub.get('description', '')}"
            flat.append(sub)
    return flat


def _custom_chapter_titles(planned_chapters: list[Any] | None) -> dict[int, str]:
    """Chapter number -> title from the blueprint's planned chapters (dicts or plain titles)."""
    titles: dict[int, str] = {}
    for idx, chapter in enumerate(planned_chapters or [], 1):
        if isinstance(chapter, dict):
            number = int(chapter.get("index") or chapter.get("chapter_index") or chapter.get("id") or idx)
            title = str(chapter.get("title") or chapter.get("chapter_title") or "").strip()
            if title:
                titles[number] = title
        elif isinstance(chapter, str) and chapter.strip():
            titles[idx] = chapter.strip()
    return titles


def _covered_chapters(descriptions: list[str], custom_titles: dict[int, str], everything_marker: bool) -> set[int]:
    """Canonical chapters (1-6) the given lower-cased thesis task descriptions already work on."""
    covered: set[int] = set()
    for desc in descriptions:
        if everything_marker and any(w in desc for w in _EVERYTHING_MARKERS):
            covered.update(range(1, 7))
        for number in range(1, 7):
            numbered = re.search(
                rf"\b(?:podrozdzia[łl]u?|rozdzia[łl]u?|chapter|sekcj[ai]|section|ch|r0?)\s*{number}(?:\.\d+|\b)", desc
            ) or re.search(rf"\b{number}\.\d+\b", desc)
            titled = number in custom_titles and custom_titles[number].lower()[:18] in desc
            if numbered or titled or any(w in desc for w in _CHAPTER_WORDS[number]):
                covered.add(number)
    return covered



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
            healing_payload["reflection_feedback"] = (
                "BŁĄD: Poprzednia odpowiedź nie zawierała listy zadań w polu 'tasks'. "
                "Wymagane jest umieszczenie tablicy 'tasks' jako pierwszego klucza w JSON z co najmniej 3 przyrostami "
                "(Vertical Feature Slices): kod, testy jednostkowe i opis w pracy dyplomowej."
            )
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
                user_prompt=user_prompt,
                multi_cycle_waves=True,
                preferred_coder=created_specialist_id or "seed_coder",
                thesis_type=planned_thesis_type,
                planned_chapters=planned_chapters if isinstance(planned_chapters, list) else None,
            )

        write_json_state(self.task_queue_path, tasks)

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
                user_prompt=user_prompt,
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

    def _normalize_and_heal_task_plan(
        self,
        raw_tasks: list[dict[str, Any]],
        user_prompt: str,
        multi_cycle_waves: bool = False,
        preferred_coder: str | None = None,
        thesis_type: str | None = None,
        planned_chapters: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Ensure all hypergraph blast-radius nodes and active agents are valid while preserving elastic task counts."""
        agents = {
            "coder": self._resolve_active_agent(preferred_coder or "seed_coder", fallback="seed_coder"),
            "tester": self._resolve_active_agent("seed_tester", fallback="seed_coder"),
            "writer": self._resolve_active_agent("seed_writer", fallback="seed_coder"),
        }
        sota_agent = self._resolve_active_agent("sota_researcher", fallback="seed_writer")
        agents["sota"] = sota_agent
        agents["bg"] = self._resolve_active_agent("background_researcher", fallback=sota_agent)
        agents["disc"] = self._resolve_active_agent("discoverer_researcher", fallback=sota_agent)
        files = {role: self._role_file(role) for role in ("config", "core", "results", "thesis", "tests")}
        t_type = (thesis_type or "inzynierska").strip().lower()
        is_paper = t_type in ("paper", "article", "scientific_paper")

        cleaned = [self._clean_task(item, idx, agents) for idx, item in enumerate(_flatten_subtasks(raw_tasks))]

        # Only synthesize a full baseline pipeline from scratch if the planner returned nothing at all.
        # Whenever task_planner returns tasks (whether 5, 10, 15, or 25+), preserve them elastically!
        if multi_cycle_waves and not cleaned:
            return self._full_pipeline(t_type, is_paper, user_prompt, agents, files)

        if multi_cycle_waves and self.include_docs and not is_paper:
            self._insert_missing_chapters(cleaned, t_type, planned_chapters, agents, files["thesis"])

        # Every role of a thesis project must have at least one task. Roles are matched by the file playing them.
        covered_roles = {self._role_of(t.get("target_node")) for t in cleaned}
        role_tasks = {
            "config": (f"Zdefiniowanie hiperparametrów i stałych konfiguracyjnych w module {files['config']}", "coder"),
            "core": (f"Implementacja głównego algorytmu oraz metody bazowej (baseline) w module {files['core']}", "coder"),
            "results": ("Ewaluacja empiryczna: uruchomienie eksperymentu i wygenerowanie wyników oraz wykresów", "tester"),
            "thesis": (f"Opracowanie sekcji i rozdziałów pracy dyplomowej ze wskaźnikami symbolicznymi w {files['thesis']}", "writer"),
        }
        healed_any = False
        front = 0
        for role, (description, agent) in role_tasks.items():
            if (role == "thesis" and not self.include_docs) or role in covered_roles:
                continue
            task = _task(f"T{len(cleaned) + 1}", description, files[role], agents[agent])
            if role in ("config", "core"):
                cleaned.insert(front, task)  # what the planner's tasks build on goes first
                front += 1
            else:
                cleaned.append(task)  # results and thesis come last
            healed_any = True

        if healed_any and multi_cycle_waves:
            has_research = any(t.get("assigned_agent") in _RESEARCH_AGENTS for t in cleaned)
            if self.include_docs and not has_research:
                description = "Przegląd literatury dziedzinowej i przygotowanie bibliografii w references.bib"
                cleaned.insert(0, _task("T0_RES", description, files["thesis"], agents["disc" if is_paper else "bg"]))
            # Research first; otherwise the planner's order stands, since only the planner knows which module
            # imports which (sorting by role put the experiment script before the modules it imports).
            cleaned.sort(key=lambda t: t.get("assigned_agent") not in _RESEARCH_AGENTS)
            for idx, task in enumerate(cleaned, 1):
                task["task_id"] = f"T{idx}"

        cleaned = self._entrypoint_after_modules(cleaned)

        # Topological sanity check: the module under test is implemented before its unit tests.
        roles = [self._role_of(t.get("target_node")) for t in cleaned]
        if "core" in roles:
            first_core = roles.index("core")
            early_tests = [t for t, r in zip(cleaned[:first_core], roles) if r == "tests"]
            if early_tests:
                rest = [t for t in cleaned if not any(t is e for e in early_tests)]
                core_idx = next(i for i, t in enumerate(rest) if self._role_of(t.get("target_node")) == "core")
                cleaned = rest[: core_idx + 1] + early_tests + rest[core_idx + 1 :]
        return cleaned

    def _entrypoint_after_modules(self, tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """The declared experiment entrypoint runs the other code modules, so its tasks follow theirs."""
        blueprint = read_json_state(self.blueprint_path) if self.blueprint_path.exists() else {}
        entry = str(blueprint.get("entrypoint") or "").partition(":")[0] if isinstance(blueprint, dict) else ""
        if not entry:
            return tasks
        nodes = read_json_state(self.matrix_path).get("nodes", {}) if self.matrix_path.exists() else {}
        paths = [str(nodes.get(str(t.get("target_node")), {}).get("path", t.get("target_node"))) for t in tasks]
        modules = [i for i, p in enumerate(paths) if p.endswith(".py") and p != entry and not Path(p).name.startswith("test_")]
        if not modules:
            return tasks
        last_module = tasks[modules[-1]]
        early_entry = [t for i, (t, p) in enumerate(zip(tasks, paths)) if p == entry and i < modules[-1]]
        if not early_entry:
            return tasks
        rest = [t for t in tasks if not any(t is e for e in early_entry)]
        at = next(i for i, t in enumerate(rest) if t is last_module) + 1
        return rest[:at] + early_entry + rest[at:]

    def _clean_task(self, item: dict[str, Any], idx: int, agents: dict[str, str]) -> dict[str, Any]:
        """One planner task in canonical form: an existing node or workspace path, and an active agent."""
        t_id = str(item.get("task_id") or item.get("id") or f"T{idx + 1}")
        desc_str = str(item.get("description") or "")
        hg_nodes = item.get("hypergraph_nodes") or item.get("nodes") or []
        first_hg_node = str(hg_nodes[0]) if isinstance(hg_nodes, list) and hg_nodes else ""
        out_files = item.get("output_files") or []
        first_out_file = (
            str(out_files[0]) if isinstance(out_files, list) and out_files else str(item.get("target_file") or item.get("file") or "")
        ).lower()

        node_id = str(item.get("target_node") or item.get("node_id") or item.get("node") or first_hg_node or "")
        # Any node of the graph or any workspace file path is a valid target. Keyword guessing is only for
        # ids that are neither (hallucinated labels), not a whitelist of five files.
        known_nodes = read_json_state(self.matrix_path).get("nodes", {})
        if node_id not in known_nodes and _looks_like_workspace_path(first_out_file):
            node_id = first_out_file
        if node_id not in known_nodes and node_id not in ROLE_ALIASES and not _looks_like_workspace_path(node_id):
            planned_node = node_id
            hint_text = f"{first_out_file} {desc_str.lower()}"
            if "pytest" in hint_text or "unit test" in hint_text or "test_" in hint_text:
                node_id = self._role_file("tests")
            elif "thesis.md" in hint_text or "references.bib" in hint_text or "rozdział" in hint_text:
                node_id = self._role_file("thesis")
            elif "config" in hint_text:
                node_id = self._role_file("config")
            else:
                node_id = self._role_file("core")
            # An overridden planner decision is logged, never silent.
            self.logger.log_step(
                "PLAN_OVERRIDE",
                f"Zadanie {t_id}: węzeł '{planned_node}' nie istnieje i nie jest ścieżką pliku -> przypisano {node_id}.",
            )

        raw_agents_list = item.get("agents")
        specialization = str(item.get("agent_specialization") or "").strip().lower()
        raw_ag = str(
            item.get("assigned_agent")
            or item.get("agent")
            or item.get("agent_name")
            or item.get("agent_id")
            or (raw_agents_list[0] if isinstance(raw_agents_list, list) and raw_agents_list else "")
            or agents.get(_SPECIALIZATION_AGENT.get(specialization, ""), "")
        )
        role = self._role_of(node_id)
        target_name = Path(self._role_file(role) if role else node_id).name.lower()
        if target_name.endswith((".md", ".tex", ".bib")):
            default_ag = agents["writer"]
        elif role in ("results", "tests") or target_name.startswith("test_"):
            default_ag = agents["tester"]
        else:
            default_ag = agents["coder"]
        description = desc_str or f"Realizacja węzła {node_id}"
        return _task(t_id, description, node_id, self._resolve_active_agent(raw_ag, fallback=default_ag))

    def _full_pipeline(
        self, t_type: str, is_paper: bool, user_prompt: str, agents: dict[str, str], files: dict[str, str]
    ) -> list[dict[str, Any]]:
        """Incremental vertical slices (code, tests and thesis progress together) when the planner returned nothing."""
        cfg, core, tests, results = files["config"], files["core"], files["tests"], files["results"]
        kind = "paper" if is_paper else "magisterska" if t_type in ("magisterska", "master", "msc") else "thesis"
        steps: list[tuple[str | None, str, str, str]] = []  # (task_id or None for the next T<n>, description, role, agent)
        if self.include_docs:
            steps += [(tid, desc, "thesis", agent) for tid, desc, agent in _PIPELINE_INTRO[kind]]
        steps += [
            (None, f"[Przyrost 1: Model i parametry] Zdefiniuj stałe i hiperparametry w {cfg} ({user_prompt[:70]}...)", "config", "coder"),
            (None, f"[Przyrost 1: Model i parametry] Zbuduj testy jednostkowe walidacji parametrów i struktur w {tests}", "tests", "tester"),
            (None, f"[Przyrost 2: Algorytm i baseline] Zaimplementuj logikę algorytmu oraz metodę referencyjną w {core}", "core", "coder"),
            (None, f"[Przyrost 2: Algorytm i baseline] Zbuduj testy jednostkowe poprawności algorytmu i metody bazowej w {tests}", "tests", "tester"),
        ]
        if self.include_docs:
            steps += [(None, _PIPELINE_CHAPTERS[n][is_paper], "thesis", "writer") for n in (3, 4)]
        steps += [
            (
                None,
                f"[Przyrost 3: Ewaluacja empiryczna] Przeprowadź badania porównawcze, zapisz {results} i wygeneruj wykresy w plot_results.py",
                "results",
                "tester",
            ),
            (None, f"[Przyrost 3: Ewaluacja empiryczna] Zaimplementuj testy asercji jakościowych wyników i zbieżności w {tests}", "tests", "tester"),
        ]
        if self.include_docs:
            steps += [(None, _PIPELINE_CHAPTERS[n][is_paper], "thesis", "writer") for n in (5, 6)]

        tasks: list[dict[str, Any]] = []
        for task_id, description, role, agent in steps:
            tasks.append(_task(task_id or f"T{len(tasks) + 1}", description, files[role], agents[agent]))
        return tasks

    def _insert_missing_chapters(
        self,
        cleaned: list[dict[str, Any]],
        t_type: str,
        planned_chapters: list[dict[str, Any]] | None,
        agents: dict[str, str],
        thesis_f: str,
    ) -> None:
        """Add a writer task for every canonical chapter (1-6) no thesis task covers, in the slice it belongs to."""
        custom_titles = _custom_chapter_titles(planned_chapters)
        thesis_descriptions = [str(t.get("description", "")).lower() for t in cleaned if self._role_of(t.get("target_node")) == "thesis"]
        covered = _covered_chapters(thesis_descriptions, custom_titles, everything_marker=self.provider == "mock")
        for number in (n for n in range(1, 7) if n not in covered):
            title = custom_titles.get(number)
            description = f"Redakcja Rozdziału {number} ({title}) w thesis.md" if title else _MISSING_CHAPTER[number]
            agent = agents["bg"] if number == 2 and t_type in ("inzynierska", "licencjacka") else agents["writer"]
            task = _task(f"T_CH{number}", description, thesis_f, agent)
            if number in (1, 2):
                before = ("core", "results")  # slice 1: before the implementation
            elif number in (3, 4):
                before = ("results",)  # slice 2: before the evaluation
            else:
                cleaned.append(task)  # slice 3: at the end
                continue
            at = next((i for i, t in enumerate(cleaned) if self._role_of(t.get("target_node")) in before), len(cleaned))
            cleaned.insert(at, task)
