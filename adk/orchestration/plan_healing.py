"""Plan healing: the planner's tasks in canonical form and the missing thesis chapters added. What the project
contains and in which order it is built come from the specification (plan_spec, schedule), not from here."""

from __future__ import annotations


import re
from pathlib import Path
from typing import Any

from adk.orchestration import agent_texts as texts
from adk.orchestration import agent_task_templates as templates
from adk.core.models import read_json_state
from adk.orchestration.common import (
    THESIS_FILE,
    _agent_for_path,
    _looks_like_workspace_path,
)
from adk.orchestration.routing import DERIVED_SUFFIXES, _canonical_path, _names_file


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


# Words that mark a task description as working on a canonical chapter.
_CHAPTER_WORDS = {
    1: ("wstęp", "wstep", "cel", "teza", "intro", "problem"),
    2: ("sota", "stan wiedzy", "literatur", "przegląd", "przeglad", "related", "background"),
    3: ("architektur", "formalizm", "matematyczn", "system", "design", "model", "tikz"),
    4: ("implementacj", "algorytm", "struktury", "implementation", "ast"),
    5: ("wyniki", "ewaluacj", "eksperyment", "badani", "evaluation", "metodologia", "empirical", "results"),
    6: ("podsumowan", "wnioski", "conclusi", "kierunki", "summary"),
}


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


def _covered_chapters(descriptions: list[str], custom_titles: dict[int, str]) -> set[int]:
    """Chapters (planned, or the canonical 1-6) the given lower-cased thesis task descriptions already work on."""
    covered: set[int] = set()
    numbers = sorted(set(range(1, 7)) | set(custom_titles))
    for desc in descriptions:
        for number in numbers:
            numbered = re.search(
                rf"\b(?:podrozdzia[łl]u?|rozdzia[łl]u?|chapter|sekcj[ai]|section|ch|r0?)\s*{number}(?:\.\d+|\b)", desc
            ) or re.search(rf"\b{number}\.\d+\b", desc)
            titled = number in custom_titles and custom_titles[number].lower()[:18] in desc
            if numbered or titled or any(w in desc for w in _CHAPTER_WORDS.get(number, ())):
                covered.add(number)
    return covered


class PlanHealingMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

    def _normalize_and_heal_task_plan(
        self,
        raw_tasks: list[dict[str, Any]],
        multi_cycle_waves: bool = False,
        preferred_coder: str | None = None,
        thesis_type: str | None = None,
        planned_chapters: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """The planner's tasks in canonical form (existing targets, active agents), with a writer task for every
        chapter no task covers. Nothing else is invented: the specification decides what the project holds (02,
        2026-11-16: an invented "config.py" task rewrote the planned config module before its own task ran)."""
        agents = {
            "coder": self._resolve_active_agent(preferred_coder or "seed_coder", fallback="seed_coder"),
            "tester": self._resolve_active_agent("seed_tester", fallback="seed_coder"),
            "writer": self._resolve_active_agent("seed_writer", fallback="seed_coder"),
        }
        sota_agent = self._resolve_active_agent("sota_researcher", fallback="seed_writer")
        agents["sota"] = sota_agent
        agents["bg"] = self._resolve_active_agent("background_researcher", fallback=sota_agent)
        agents["disc"] = self._resolve_active_agent("discoverer_researcher", fallback=sota_agent)
        t_type = (thesis_type or "inzynierska").strip().lower()
        cleaned = [self._clean_task(item, idx, agents) for idx, item in enumerate(_flatten_subtasks(raw_tasks))]
        if multi_cycle_waves and self.include_docs and t_type not in ("paper", "article", "scientific_paper"):
            self._insert_missing_chapters(cleaned, t_type, planned_chapters, agents, THESIS_FILE)
        return [t for t in cleaned if t is not None]

    def _planned_files(self) -> tuple[list[str], str | None]:
        """The plan's code modules and its entrypoint module (the blueprint, before H is built from it)."""
        blueprint = read_json_state(self.blueprint_path) if self.blueprint_path.exists() else {}
        modules = sorted((blueprint.get("interfaces") or {}).keys()) if isinstance(blueprint, dict) else []
        entry = str(blueprint.get("entrypoint") or "").partition(":")[0] if isinstance(blueprint, dict) else ""
        return modules, entry or None

    def _clean_task(self, item: dict[str, Any], idx: int, agents: dict[str, str]) -> dict[str, Any] | None:
        """One planner task in canonical form: a workspace path (a planned module, a test, the thesis) and an active
        agent. A target that is not a path is looked up among the planned files its description names; a task
        that names none has no target in the plan and is dropped, logged (no routing by keywords or roles)."""
        t_id = str(item.get("task_id") or item.get("id") or f"T{idx + 1}")
        desc_str = str(item.get("description") or "")
        hg_nodes = item.get("hypergraph_nodes") or item.get("nodes") or []
        out_files = item.get("output_files") or []
        candidates = [
            item.get("target_node"), item.get("node_id"), item.get("node"),
            hg_nodes[0] if isinstance(hg_nodes, list) and hg_nodes else None,
            out_files[0] if isinstance(out_files, list) and out_files else None,
            item.get("target_file"), item.get("file"),
        ]
        target = next((_canonical_path(str(c)) for c in candidates if c and _looks_like_workspace_path(_canonical_path(str(c)))), "")
        modules, entry = self._planned_files()
        if not target:
            named = [m for m in sorted(modules, key=len, reverse=True) if _names_file(desc_str.lower(), m.lower()) or _names_file(desc_str.lower(), Path(m).name.lower())]
            agent_hint = str(item.get("assigned_agent") or "")
            target = named[0] if named else (THESIS_FILE if "writer" in agent_hint or "research" in agent_hint else "")
            self.logger.log_step("PLAN_OVERRIDE", f"Zadanie {t_id}: cel '{candidates[0]}' nie jest ścieżką pliku -> {target or 'zadanie pominięte'}.")
            if not target:
                return None
        if "/" not in target and Path(target).name.startswith("test_"):
            target = f"tests/{target}"  # test modules live in tests/ (U4)
        elif Path(target).suffix.lower() in DERIVED_SUFFIXES and entry:
            # Results and figures come from running code; a task "producing" them is a task on the entrypoint,
            # which writes them, by the coder (U5, 2026-11-15: T16 on results.csv went to the tester).
            self.logger.log_step("PLAN_OVERRIDE", f"Zadanie {t_id}: artefakt pochodny '{target}' -> moduł {entry} (koder).")
            return _task(t_id, desc_str or texts.node_task(entry), entry, agents["coder"])

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
        default_ag = {"seed_writer": agents["writer"], "seed_tester": agents["tester"]}.get(_agent_for_path(target), agents["coder"])
        return _task(t_id, desc_str or texts.node_task(target), target, self._resolve_active_agent(raw_ag, fallback=default_ag))

    def _insert_missing_chapters(
        self,
        cleaned: list[dict[str, Any]],
        t_type: str,
        planned_chapters: list[dict[str, Any]] | None,
        agents: dict[str, str],
        thesis_f: str,
    ) -> None:
        """Add a writer task for every planned chapter (the canonical 1-6 without an outline) no thesis task covers,
        in the slice it belongs to."""
        custom_titles = _custom_chapter_titles(planned_chapters)
        thesis_descriptions = [str(t.get("description", "")).lower() for t in cleaned if t and str(t.get("target_node", "")).startswith(thesis_f)]
        covered = _covered_chapters(thesis_descriptions, custom_titles)
        for number in (n for n in (sorted(custom_titles) or range(1, 7)) if n not in covered):
            title = custom_titles.get(number)
            description = templates.titled_chapter_task(number, title) if title else templates.MISSING_CHAPTER_TASK[number]
            agent = agents["bg"] if number == 2 and t_type in ("inzynierska", "licencjacka") else agents["writer"]
            task = _task(f"T_CH{number}", description, thesis_f, agent)
            _modules, entry = self._planned_files()
            if number in (1, 2):
                # slice 1: before the implementation (the first code task)
                at = next((i for i, t in enumerate(cleaned) if t and str(t.get("target_node", "")).endswith(".py")), len(cleaned))
            elif number in (3, 4):
                # slice 2: before the evaluation (the task on the entrypoint, which writes the results)
                at = next((i for i, t in enumerate(cleaned) if t and t.get("target_node") == entry), len(cleaned))
            else:
                cleaned.append(task)  # slice 3: at the end
                continue
            cleaned.insert(at, task)
