"""Plan healing: the planner's tasks in canonical form, missing roles and chapters added, the skeleton first."""

from __future__ import annotations


import re
from pathlib import Path
from typing import Any

from adk.orchestration import agent_texts as texts
from adk.orchestration import agent_task_templates as templates
from adk.core.models import read_json_state
from adk.orchestration.common import (
    _looks_like_workspace_path,
    ROLE_ALIASES,
    is_skeleton_task,
    SKELETON_TASK_ID,
)
from adk.tools.verification.contract_check import is_contract_module


_SKELETON_WORDS = re.compile(r"\b(?:szkielet\w*|skeleton|stubs?)\b", re.IGNORECASE)


_DERIVED_SUFFIXES = {".csv", ".png", ".pdf", ".svg"}


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


class PlanHealingMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

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
            role: (templates.role_task(role, files["core" if role == "results" else role]), agent)
            for role, agent in (("config", "coder"), ("core", "coder"), ("results", "coder"), ("thesis", "writer"))
        }
        if "core" in covered_roles:
            covered_roles.add("results")  # results are written by the entrypoint module, never by a task of their own (U5)
        healed_any = False
        front = 0
        for role, (description, agent) in role_tasks.items():
            if (role == "thesis" and not self.include_docs) or role in covered_roles:
                continue
            task = _task(f"T{len(cleaned) + 1}", description, files["core" if role == "results" else role], agents[agent])
            if role in ("config", "core"):
                cleaned.insert(front, task)  # what the planner's tasks build on goes first
                front += 1
            else:
                cleaned.append(task)  # results and thesis come last
            healed_any = True

        if healed_any and multi_cycle_waves:
            has_research = any(t.get("assigned_agent") in _RESEARCH_AGENTS for t in cleaned)
            if self.include_docs and not has_research:
                cleaned.insert(0, _task("T0_RES", texts.RESEARCH_TASK, files["thesis"], agents["disc" if is_paper else "bg"]))
            # Research first; otherwise the planner's order stands, since only the planner knows which module
            # imports which (sorting by role put the experiment script before the modules it imports).
            cleaned.sort(key=lambda t: t.get("assigned_agent") not in _RESEARCH_AGENTS)
            for idx, task in enumerate(cleaned, 1):
                task["task_id"] = f"T{idx}"

        cleaned = self._entrypoint_after_modules(cleaned)
        if multi_cycle_waves:
            cleaned = self._skeleton_first(cleaned, agents["coder"])

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

    def _skeleton_first(self, tasks: list[dict[str, Any]], coder: str) -> list[dict[str, Any]]:
        """The interface of every planned code module is laid out once, before any module is implemented: one
        task writes all modules as signatures with `raise NotImplementedError` bodies, later tasks fill them in.
        Without it each builder guessed its neighbours' API (2026-11-12: eight versions of one agent class)."""
        nodes = read_json_state(self.matrix_path).get("nodes", {}) if self.matrix_path.exists() else {}

        def _path(task: dict[str, Any]) -> str:
            target = str(task.get("target_node"))
            if target in nodes:
                return str(nodes[target].get("path", target))
            return self._role_file(ROLE_ALIASES[target]) if target in ROLE_ALIASES else target

        paths = [_path(t) for t in tasks]
        modules = list(dict.fromkeys(p for p in paths if is_contract_module(p)))
        if len(modules) < 2:
            return tasks  # one module has no interface between tasks to agree on
        blueprint = read_json_state(self.blueprint_path) if self.blueprint_path.exists() else {}
        entrypoint = str(blueprint.get("entrypoint") or "") if isinstance(blueprint, dict) else ""
        entry_file = entrypoint.partition(":")[0]
        module_list = ", ".join(modules)
        planned = next((t for t in tasks if is_skeleton_task(t) or _SKELETON_WORDS.search(str(t.get("description", "")))), None)
        if planned is not None:
            tasks = [t for t in tasks if t is not planned]
            planned["task_id"] = SKELETON_TASK_ID
            if module_list not in str(planned.get("description", "")):
                planned["description"] = f"{planned.get('description', '')}{texts.skeleton_modules(module_list)}"
            skeleton = planned
        else:
            skeleton = _task(
                SKELETON_TASK_ID,
                texts.skeleton_task(module_list, entry_file, entrypoint),
                entry_file if entry_file in modules else modules[0],
                coder,
            )
        skeleton["assigned_agent"] = skeleton.get("assigned_agent") or coder
        first_code = next((i for i, t in enumerate(tasks) if is_contract_module(_path(t))), len(tasks))
        return tasks[:first_code] + [skeleton] + tasks[first_code:]

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

        target_path = str(known_nodes.get(node_id, {}).get("path", node_id)).replace("\\", "/")
        if _looks_like_workspace_path(target_path) and "/" not in target_path and Path(target_path).name.startswith("test_"):
            node_id = f"tests/{target_path}"  # test modules live in tests/ (U4)
        elif self._role_of(node_id) == "results" or Path(target_path).suffix.lower() in _DERIVED_SUFFIXES:
            # Results and figures come from running code; a task "producing" them is a task on the module that
            # writes them, by the coder (U5, 2026-11-15: T16 on results.csv went to the tester).
            node_id = self._role_file("core")
            self.logger.log_step("PLAN_OVERRIDE", f"Zadanie {t_id}: artefakt pochodny '{target_path}' -> moduł {node_id} (koder).")
            return _task(t_id, desc_str or texts.node_task(node_id), node_id, agents["coder"])

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
        description = desc_str or texts.node_task(node_id)
        return _task(t_id, description, node_id, self._resolve_active_agent(raw_ag, fallback=default_ag))

    def _full_pipeline(
        self, t_type: str, is_paper: bool, user_prompt: str, agents: dict[str, str], files: dict[str, str]
    ) -> list[dict[str, Any]]:
        """Incremental vertical slices (code, tests and thesis progress together) when the planner returned nothing."""
        cfg, core, tests = files["config"], files["core"], files["tests"]
        kind = "paper" if is_paper else "magisterska" if t_type in ("magisterska", "master", "msc") else "thesis"
        steps: list[tuple[str | None, str, str, str]] = []  # (task_id or None for the next T<n>, description, role, agent)
        if self.include_docs:
            steps += [(tid, desc, "thesis", agent) for tid, desc, agent in templates.PIPELINE_INTRO[kind]]
        steps += [(None, desc, role, agent) for desc, role, agent in templates.full_pipeline_code_steps(cfg, core, tests, user_prompt)]
        if self.include_docs:
            steps += [(None, templates.PIPELINE_CHAPTERS[n][is_paper], "thesis", "writer") for n in (3, 4)]
        steps += [(None, desc, role, agent) for desc, role, agent in templates.full_pipeline_evaluation_steps(core, tests)]
        if self.include_docs:
            steps += [(None, templates.PIPELINE_CHAPTERS[n][is_paper], "thesis", "writer") for n in (5, 6)]

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
            description = templates.titled_chapter_task(number, title) if title else templates.MISSING_CHAPTER_TASK[number]
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
