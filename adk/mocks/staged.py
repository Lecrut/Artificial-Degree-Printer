"""A whole plan (interfaces, entrypoint, figures, blueprint) answered stage by stage, as the planning agents of §XVI
would answer it: the outline derived from the interfaces, each module's interface from its source, critics that
pass. Simulated agents and tests that describe a plan as a whole use it; the harness never sees this module."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

_IMPORT = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.M)


def _provides(source: str) -> list[str]:
    """Public constants, top-level functions and classes, and the public methods of the classes."""
    names: list[str] = []
    for node in ast.parse(source).body:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
        names += [t.id for t in targets if isinstance(t, ast.Name) and not t.id.startswith("_")]
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            names.append(node.name)
        elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            names.append(node.name)
            names += [f"{node.name}.{f.name}" for f in node.body if isinstance(f, ast.FunctionDef) and not f.name.startswith("_")]
    return names


def outline_from_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """The outline a plan's interfaces imply: one module per interface, `depends_on` from its imports."""
    interfaces: dict[str, str] = plan.get("interfaces") or {}
    by_import = {rel.removesuffix(".py").replace("/", "."): rel for rel in interfaces} | {Path(rel).stem: rel for rel in interfaces}
    blueprint = dict(plan.get("academic_blueprint") or {})
    entry = str(plan.get("entrypoint") or blueprint.pop("entrypoint", "") or "")
    plots = str(plan.get("plots") or blueprint.pop("plots", "") or "")
    blueprint.pop("entrypoint", None)
    blueprint.pop("plots", None)
    modules = []
    for rel, source in interfaces.items():
        deps = [by_import[d or p] for d, p in _IMPORT.findall(source) if by_import.get(d or p) not in (None, rel)]
        modules.append({"file": rel, "purpose": f"{Path(rel).stem} module", "depends_on": sorted(set(deps)), "provides": _provides(source)})
    return {
        "modules": modules, "entrypoint": entry, "plots": plots, "academic_blueprint": blueprint,
        **{k: plan[k] for k in ("thesis_type", "template_name", "missing_agent_specialization") if plan.get(k)},
    }


def staged_answer(plan: dict[str, Any], agent: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    """The answer of a planning agent for `plan`, or None for any other agent."""
    if agent == "plan_outline":
        return outline_from_plan(plan)
    if agent == "plan_module":
        rel = str((payload.get("module") or {}).get("file") or "")
        return {"source": (plan.get("interfaces") or {}).get(rel, ""), "needs": {}}
    if agent in ("outline_critic_guard", "module_critic_guard", "plan_critic_guard"):
        return {"status": "PASS", "issues": []}
    return None
