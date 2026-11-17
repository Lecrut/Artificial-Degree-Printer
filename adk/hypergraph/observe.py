"""H_obs: the workspace as it is, read with the same parser as the plan (`spec_from_stub`), and its difference from
H. The observation is never stored as truth — it is only compared (Audit VI §VII.12.9)."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from adk.hypergraph.build import resolve_import, spec_from_stub
from adk.hypergraph.model import Hypergraph, Violation
from adk.tools.building.import_sync import module_import_path

_SKIP_DIRS = {"__pycache__", "logs", "figures", ".pytest_cache"}


def observe(workspace: str | Path, h: Hypergraph) -> dict[str, dict[str, Any] | None]:
    """Observed σ of every .py file in the workspace (None: the file does not parse — the syntax guard reports it)."""
    root = Path(workspace)
    modules = {module_import_path(e.id.removeprefix("I:")): e.id.removeprefix("I:") for e in h.edges.values() if e.type == "I"}
    observed: dict[str, dict[str, Any] | None] = {}
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        if _SKIP_DIRS & set(path.relative_to(root).parts):
            continue
        try:
            source = path.read_text(encoding="utf-8")
            observed[rel] = spec_from_stub(rel, source, modules)
            if path.name.startswith("test_"):
                observed[rel]["attrs_used"] = _attributes_used(ast.parse(source), rel, modules)
        except (SyntaxError, ValueError):
            observed[rel] = None
    return observed


def _attributes_used(tree: ast.Module, rel: str, modules: dict[str, str]) -> list[tuple[str, str, str]]:
    """(producer, Class, attribute) for every attribute a test reads on an object it built from a planned class:
    `m = ZScoreBaseline(3.0); m.mean_` or `hasattr(m, 'mean_')` (02, T10: `mean_` was declared nowhere)."""
    imported: dict[str, tuple[str, str]] = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            producer = resolve_import(rel, node.module, node.level, modules)
            for alias in node.names if producer else []:
                imported[alias.asname or alias.name] = (producer, alias.name)
    used: list[tuple[str, str, str]] = []
    for func in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        objects: dict[str, tuple[str, str]] = {}
        for node in ast.walk(func):
            if (
                isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id in imported
            ):
                objects[node.targets[0].id] = imported[node.value.func.id]
        for node in ast.walk(func):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in objects:
                used.append((*objects[node.value.id], node.attr))
            elif (
                isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("hasattr", "getattr")
                and len(node.args) >= 2 and isinstance(node.args[0], ast.Name) and node.args[0].id in objects
                and isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, str)
            ):
                used.append((*objects[node.args[0].id], node.args[1].value))
    return used


def _module_diff(rel: str, planned: dict[str, Any], seen: dict[str, Any]) -> list[Violation]:
    found: list[Violation] = []
    plan_symbols, seen_symbols = planned.get("symbols", {}), seen.get("symbols", {})
    missing = sorted(set(plan_symbols) - set(seen_symbols))
    # Undeclared data attributes are internal state; only declared ones are part of the interface.
    extra = sorted(n for n in set(seen_symbols) - set(plan_symbols) if seen_symbols[n]["kind"] != "attr")
    if missing:
        found.append(Violation("API_MISSING", f"the interface declares {', '.join(missing)}, the file lacks them", rel, rel))
    if extra:
        found.append(Violation("API_EXTRA", f"public {', '.join(extra)} not in the interface (helpers start with `_`)", rel, rel))
    for name in sorted(set(plan_symbols) & set(seen_symbols)):
        want, got = plan_symbols[name], seen_symbols[name]
        if want["kind"] != got["kind"]:
            found.append(Violation("API_KIND", f"{name} must be a {want['kind']}, it is a {got['kind']}", rel, rel))
        elif want.get("params") is not None and want.get("params") != got.get("params"):
            found.append(Violation(
                "API_SIGNATURE", f"{name}({', '.join(got['params'])}) differs from the interface ({', '.join(want['params'])})", rel, rel
            ))
    return found


def _import_diff(rel: str, seen: dict[str, Any], h: Hypergraph, is_module: bool) -> list[Violation]:
    found: list[Violation] = []
    for producer, names in seen.get("uses", {}).items():
        edge = h.edges.get(f"I:{producer}")
        if edge is None:
            continue
        outside = [n for n in names if n not in edge.spec.get("symbols", {}) and n != "*"]
        if outside:
            found.append(Violation(
                "IMPORT_OUTSIDE_SPEC",
                f"imports {', '.join(outside)} from {producer}; its interface has {', '.join(sorted(edge.spec.get('symbols', {})))}",
                rel, rel,
            ))
        if is_module and rel not in edge.members:
            found.append(Violation("IMPORT_NOT_IN_PLAN", f"imports {producer}, which the plan does not make it use", rel, rel))
    return found


def diff(h: Hypergraph, observed: dict[str, dict[str, Any] | None]) -> list[Violation]:
    """H_obs − H: files outside the plan, API that differs from σ, imports outside σ."""
    found: list[Violation] = []
    for rel, seen in observed.items():
        vertex = h.vertices.get(rel)
        if vertex is None:
            if Path(rel).name != "__init__.py":
                found.append(Violation("FILE_OUTSIDE_PLAN", "no planned artefact has this path", rel, rel))
            continue
        if seen is None:
            continue
        if vertex.kind in ("code", "entry"):
            found += _module_diff(rel, h.edges[f"I:{rel}"].spec, seen)
        found += _import_diff(rel, seen, h, vertex.kind in ("code", "entry"))
        outside = sorted({
            f"{cls}.{attr}"
            for producer, cls, attr in seen.get("attrs_used", [])
            if f"I:{producer}" in h.edges and f"{cls}.{attr}" not in h.edges[f"I:{producer}"].spec.get("symbols", {})
        })
        if outside:
            found.append(Violation(
                "TEST_OUTSIDE_SPEC", f"reads {', '.join(outside)}, which the interface does not declare (test only declared methods and attributes)", rel, rel
            ))
    return found
