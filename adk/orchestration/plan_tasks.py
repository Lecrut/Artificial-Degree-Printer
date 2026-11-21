"""Stage 3 of planning (§XVI): the task queue, derived by code from the outline and the accepted interfaces. Which
tasks a project needs follows from its modules and chapters; the planner used to write them by hand, and task
descriptions that disagreed with the interfaces blocked plans for whole rounds (2026-11-20/21)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import re

from adk.orchestration import agent_task_templates as templates
from adk.orchestration.common import THESIS_FILE
from adk.orchestration.plan_outline import module_entry, module_order
from adk.tools.verification.contract_check import public_api

# Chapters that need no code: the introduction and the literature. The others describe or report the code and are
# written once it exists (a chapter on the method cites symbols that must be there; one on results waits for them).
_NEEDS_NO_CODE = re.compile(r"wst[ęe]p|\bcel\b|literatur|przegl[ąa]d|stan\w*\s+(?:wiedzy|bada)|introduc|background|related work|state of the art", re.I)

# Literature review before the writing: foundations (I stopień), foundations then recent work (II), recent work (paper).
RESEARCH_STAGES = {"magisterska": ("background", "discoverer"), "paper": ("discoverer",)}


def _tested(rel: str, source: str, outline: dict[str, Any]) -> list[str]:
    """Public functions and classes of a module worth a unit test: everything but the functions the harness calls
    itself (entrypoint, figures). A module of constants only has none."""
    called = {outline["entrypoint"], outline["plots"]}
    return [name for name in (public_api(source) or {}) if "." not in name and f"{rel}:{name}" not in called]


def _chapter_tasks(outline: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """(chapters written before the code, chapters written after it) as writer tasks."""
    before, after = [], []
    chapters = outline["academic_blueprint"].get("planned_chapters") or []
    for idx, chapter in enumerate(c for c in chapters if isinstance(c, dict)):
        number = int(chapter.get("index") or idx + 1)
        title, focus = str(chapter.get("title") or "").strip(), str(chapter.get("focus") or "").strip()
        task = {"description": templates.chapter_task(number, title, focus), "target_node": THESIS_FILE, "assigned_agent": "seed_writer"}
        (before if _NEEDS_NO_CODE.search(f"{title} {focus}") else after).append(task)
    return before, after


def planned_tasks(
    outline: dict[str, Any], interfaces: dict[str, str], thesis_type: str, include_docs: bool, kept: set[str]
) -> list[dict[str, Any]]:
    """Research, then the introduction and literature chapters, then every module followed by its unit tests
    (dependencies first), then the other chapters. Existing modules kept as they are get no task."""
    coder = str(outline.get("missing_agent_specialization") or "seed_coder")
    tasks: list[dict[str, str]] = []
    early, late = _chapter_tasks(outline) if include_docs else ([], [])
    if include_docs:
        stages = RESEARCH_STAGES.get(thesis_type, ("background",))
        tasks += [
            {"description": templates.research_task(stage), "target_node": THESIS_FILE, "assigned_agent": f"{stage}_researcher"}
            for stage in stages
        ]
    tasks += early
    for rel in module_order(outline):
        if rel in kept or rel not in interfaces:
            continue
        entry = module_entry(outline, rel)
        names = list((public_api(interfaces[rel]) or {}).keys())
        tasks.append({"description": templates.module_task(rel, entry["purpose"], names), "target_node": rel, "assigned_agent": coder})
        if tested := _tested(rel, interfaces[rel], outline):
            test_rel = f"tests/test_{Path(rel).stem}.py"
            tasks.append({"description": templates.test_task(rel, tested, test_rel), "target_node": test_rel, "assigned_agent": "seed_tester"})
    tasks += late
    return [{"task_id": f"T{i}", **task, "status": "TODO"} for i, task in enumerate(tasks, 1)]
