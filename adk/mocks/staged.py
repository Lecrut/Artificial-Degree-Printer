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


def _declared(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, Any]:
    returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    kind = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    item: dict[str, Any] = {"signature": f"{kind}{node.name}({ast.unparse(node.args)}){returns}", "docstring": ast.get_docstring(node) or ""}
    if node.decorator_list:
        item["decorators"] = [ast.unparse(d) for d in node.decorator_list]
    return item


def sketch_of(source: str) -> dict[str, Any]:
    """What the module author of §XXIX declares for `source`: names, signatures and docstrings, never a body."""
    tree = ast.parse(source)
    functions = (ast.FunctionDef, ast.AsyncFunctionDef)
    return {
        "docstring": ast.get_docstring(tree) or "",
        "imports": [ast.unparse(n) for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))],
        "constants": [ast.unparse(n) for n in tree.body if isinstance(n, (ast.Assign, ast.AnnAssign))],
        "functions": [_declared(n) for n in tree.body if isinstance(n, functions)],
        "classes": [
            {
                "name": n.name, "bases": [ast.unparse(b) for b in n.bases], "docstring": ast.get_docstring(n) or "",
                "decorators": [ast.unparse(d) for d in n.decorator_list],
                "attributes": [ast.unparse(s) for s in n.body if isinstance(s, (ast.Assign, ast.AnnAssign))],
                "methods": [_declared(s) for s in n.body if isinstance(s, functions)],
            }
            for n in tree.body if isinstance(n, ast.ClassDef)
        ],
    }


def staged_answer(plan: dict[str, Any], agent: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    """The answer of a planning agent for `plan`, or None for any other agent."""
    if agent == "plan_outline":
        return outline_from_plan(plan)
    if agent == "plan_module":
        rel = str((payload.get("module") or {}).get("file") or "")
        return {**sketch_of((plan.get("interfaces") or {}).get(rel, "")), "needs": {}}
    if agent in ("outline_critic_guard", "module_critic_guard", "plan_critic_guard"):
        return {"status": "PASS", "issues": []}
    return None
