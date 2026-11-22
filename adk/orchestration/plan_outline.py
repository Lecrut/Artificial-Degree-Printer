"""Stage 1 of planning — the outline (§XVI, 2026-11-21): what the project is made of before any code. Modules with
their purpose, dependencies and the names they promise (`provides`), the entrypoint, the figures function, the
metrics and the chapters. Checked here by code; the interfaces are written module by module afterwards
(`plan_stages`), each against this outline."""

from __future__ import annotations

import re
from typing import Any

from adk.orchestration import agent_texts as texts
from adk.orchestration.routing import _canonical_path
from adk.hypergraph.build import spec_from_stub
from adk.tools.verification.contract_check import is_contract_module

_NAME = re.compile(r"[A-Za-z_][\w.]*")
_KEYWORD = re.compile(r"(?:async\s+)?(?:class|def|function|const|constant)\s+", re.I)


def provided_name(item: Any) -> str:
    """`LogisticModel.predict(X) -> np.ndarray` -> `LogisticModel.predict`: a promise is a name, its signature is a hint.
    A leading keyword is not the name (2026-11-22, 02: `class ZScoreDetector: <Class>` promised a symbol `class`, no
    interface could declare it, and the plan was rejected after six attempts)."""
    match = _NAME.match(_KEYWORD.sub("", str(item).strip(), count=1))
    return match.group(0).rstrip(".") if match else ""


def _strings(value: Any) -> list[str]:
    """A list of non-empty strings from a list, or from one string (a model writes `"depends_on": "a.py"`)."""
    items = [value] if isinstance(value, str) else value if isinstance(value, (list, tuple)) else []
    return [str(i).strip() for i in items if str(i).strip()]


def outline_of(raw: Any) -> dict[str, Any] | None:
    """The outline in canonical form, or None when the answer carries no module list. Accepts `entrypoint` and
    `plots` at the top level or in `academic_blueprint`, and `modules` as a list or as `{file: entry}`."""
    listed = raw.get("modules") if isinstance(raw, dict) else None
    if isinstance(listed, dict):
        listed = [{"file": rel, **entry} for rel, entry in listed.items() if isinstance(entry, dict)]
    if not isinstance(raw, dict) or not isinstance(listed, list):
        return None
    blueprint = dict(raw.get("academic_blueprint") if isinstance(raw.get("academic_blueprint"), dict) else {})
    modules: list[dict[str, Any]] = []
    for item in listed:
        if isinstance(item, dict) and (item.get("file") or item.get("path")):
            modules.append({
                "file": _canonical_path(str(item.get("file") or item.get("path"))),
                "purpose": str(item.get("purpose") or "").strip(),
                "depends_on": [_canonical_path(d) for d in _strings(item.get("depends_on"))],
                "provides": [p for p in _strings(item.get("provides")) if provided_name(p)],
            })
    entry = str(raw.get("entrypoint") or blueprint.pop("entrypoint", "") or "").strip()
    plots = str(raw.get("plots") or blueprint.pop("plots", "") or "").strip()
    blueprint.pop("entrypoint", None)
    blueprint.pop("plots", None)
    return {
        "modules": modules, "entrypoint": _canonical_path(entry), "plots": _canonical_path(plots),
        "academic_blueprint": blueprint, "thesis_type": raw.get("thesis_type"), "template_name": raw.get("template_name"),
        "missing_agent_specialization": raw.get("missing_agent_specialization"),
    }


def kept_as_is(outline: dict[str, Any], rel: str, existing: dict[str, str]) -> bool:
    """An existing module the outline promises nothing new from: its code stays, with no design and no task. One
    that promises more is extended — designed from its own source, keeping every name it has."""
    if rel not in existing:
        return False
    names = existing_names(rel, existing[rel])
    return all(provided_name(p) in names for p in module_entry(outline, rel)["provides"])


def existing_names(rel: str, source: str) -> set[str]:
    """Every public name an existing module defines (constants, functions, classes, methods, attributes)."""
    try:
        return set(spec_from_stub(rel, source, {})["symbols"])
    except SyntaxError:
        return set()


def module_files(outline: dict[str, Any]) -> list[str]:
    return [m["file"] for m in outline["modules"]]


def module_entry(outline: dict[str, Any], rel: str) -> dict[str, Any]:
    return next((m for m in outline["modules"] if m["file"] == rel), {"file": rel, "purpose": "", "depends_on": [], "provides": []})


def _cycle(outline: dict[str, Any]) -> list[str]:
    """Modules on a dependency cycle (empty when the dependencies form a DAG)."""
    deps = {m["file"]: [d for d in m["depends_on"] if d in module_files(outline)] for m in outline["modules"]}
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(rel: str) -> list[str]:
        state[rel] = 1
        stack.append(rel)
        for dep in deps.get(rel, []):
            if state.get(dep) == 1:
                return stack[stack.index(dep):]
            if dep not in state and (found := visit(dep)):
                return found
        stack.pop()
        state[rel] = 2
        return []

    for rel in deps:
        if rel not in state and (found := visit(rel)):
            return found
    return []


def module_order(outline: dict[str, Any]) -> list[str]:
    """Dependencies first, the entrypoint's module last, otherwise the order of the outline."""
    files = module_files(outline)
    entry = outline["entrypoint"].partition(":")[0]
    deps = {m["file"]: [d for d in m["depends_on"] if d in files] for m in outline["modules"]}
    order: list[str] = []

    def place(rel: str, seen: frozenset[str] = frozenset()) -> None:
        if rel in order or rel in seen:
            return
        for dep in deps.get(rel, []):
            place(dep, seen | {rel})
        order.append(rel)

    for rel in files:
        if rel != entry:
            place(rel)
    if entry in files:
        place(entry)
    return order


def dependents(outline: dict[str, Any], rel: str) -> list[str]:
    """The modules that depend on `rel` directly."""
    return [m["file"] for m in outline["modules"] if rel in m["depends_on"]]


def _declared_call(outline: dict[str, Any], field: str) -> list[str]:
    value = outline[field]
    file, _, func = value.partition(":")
    if not value:
        return [texts.outline_declared_call(field, value, "is missing: declare `<path>.py:<function>`")]
    if file not in module_files(outline):
        return [texts.outline_declared_call(field, value, "names no module of the outline")]
    if func not in {provided_name(p) for p in module_entry(outline, file)["provides"]}:
        return [texts.outline_declared_call(field, value, f"is not in the `provides` of {file}")]
    return []


def outline_violations(outline: dict[str, Any], existing: dict[str, str], need_chapters: bool) -> list[str]:
    """Every reason the outline cannot become a plan, found by code (each once). `need_chapters`: the run writes a
    thesis, so the outline declares its chapters and metrics."""
    files = module_files(outline)
    if not files:
        return [texts.OUTLINE_NO_MODULES]
    found: list[str] = []
    for rel in sorted({r for r in files if files.count(r) > 1}):
        found.append(texts.outline_duplicate(rel))
    for m in outline["modules"]:
        if not is_contract_module(m["file"]):
            found.append(texts.outline_bad_file(m["file"]))
        for dep in m["depends_on"]:
            if dep not in files and dep not in existing:
                found.append(texts.outline_unknown_dependency(m["file"], dep))
    if cycle := _cycle(outline):
        found.append(texts.outline_cycle(cycle))
    found += _declared_call(outline, "entrypoint") + _declared_call(outline, "plots")
    entry = outline["entrypoint"].partition(":")[0]
    if entry in files and not cycle:
        reached, frontier = {entry}, [entry]
        while frontier:
            for dep in module_entry(outline, frontier.pop())["depends_on"]:
                if dep not in reached:
                    reached.add(dep)
                    frontier.append(dep)
        plots_file = outline["plots"].partition(":")[0]
        found += [texts.outline_unreached(rel, entry) for rel in files if rel not in reached and rel != plots_file]
    blueprint = outline["academic_blueprint"]
    if need_chapters and not blueprint.get("metrics"):  # every number of the thesis is a declared metric
        found.append(texts.OUTLINE_NO_METRICS)
    if need_chapters and not blueprint.get("planned_chapters"):
        found.append(texts.OUTLINE_NO_CHAPTERS)
    return list(dict.fromkeys(found))


def changed_modules(old: dict[str, Any], new: dict[str, Any]) -> tuple[set[str], set[str]]:
    """(modules added or changed in purpose, dependencies or promises; modules removed) between two outlines."""
    before = {m["file"]: m for m in old["modules"]}
    after = {m["file"]: m for m in new["modules"]}
    changed = {rel for rel, m in after.items() if before.get(rel) != m}
    entry_moved = {old["entrypoint"].partition(":")[0], new["entrypoint"].partition(":")[0]} if old["entrypoint"] != new["entrypoint"] else set()
    plots_moved = {old["plots"].partition(":")[0], new["plots"].partition(":")[0]} if old["plots"] != new["plots"] else set()
    return (changed | ((entry_moved | plots_moved) & set(after))), set(before) - set(after)


def outline_view(outline: dict[str, Any]) -> dict[str, Any]:
    """The outline as its author and the critics read it."""
    return {
        "modules": outline["modules"], "entrypoint": outline["entrypoint"], "plots": outline["plots"],
        "academic_blueprint": outline["academic_blueprint"],
        **({"missing_agent_specialization": outline["missing_agent_specialization"]} if outline.get("missing_agent_specialization") else {}),
    }
