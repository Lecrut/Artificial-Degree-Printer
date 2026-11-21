"""H_obs: the workspace as it is, read with the same parser as the plan (`spec_from_stub`), and its difference from
H (Audit VI §VII.12.9).

What the plan promised cannot be broken: a planned name that disappears, changes kind, or changes its signature
so that its callers break; a test that reads what the interface does not declare; an import that closes a cycle.
What an agent adds is allowed and recorded in H by the orchestrator (`absorbable`): a public name more, an optional
parameter more, an import of another planned module, a helper file imported by a planned module, a test of a
planned module (Audit VIII §X: the gate refused every helper and every extra parameter of a small model)."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from adk.hypergraph.build import resolve_import, spec_from_stub
from adk.hypergraph.model import Hypergraph, Violation
from adk.hypergraph.model import module_import_path

_SKIP_DIRS = {"__pycache__", "logs", "figures", ".pytest_cache"}


def _is_test(rel: str) -> bool:
    name = Path(rel).name
    return name.startswith("test_") or name.endswith("_test.py")


def observe(workspace: str | Path) -> dict[str, dict[str, Any] | None]:
    """Observed σ of every .py file in the workspace (None: the file does not parse — the syntax guard reports it)."""
    root = Path(workspace)
    paths = [
        p for p in sorted(root.rglob("*.py"))
        if not _SKIP_DIRS & set(p.relative_to(root).parts)
    ]
    # Every workspace module resolves, so an import of a helper file is a `use` of it, not a package.
    modules = {module_import_path(p.relative_to(root).as_posix()): p.relative_to(root).as_posix() for p in paths}
    observed: dict[str, dict[str, Any] | None] = {}
    for path in paths:
        rel = path.relative_to(root).as_posix()
        try:
            source = path.read_text(encoding="utf-8")
            observed[rel] = spec_from_stub(rel, source, modules)
            if _is_test(rel):
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


def _compatible(want: dict[str, Any], got: dict[str, Any]) -> bool:
    """A callable keeps its promise when every planned parameter is still there, in the planned order, and every
    parameter it now requires was required by the plan (anything added has a default)."""
    planned, actual = want.get("params") or [], got.get("params") or []
    return actual[: len(planned)] == planned and set(got.get("required") or []) <= set(want.get("required") or [])


def _module_diff(rel: str, planned: dict[str, Any], seen: dict[str, Any]) -> list[Violation]:
    found: list[Violation] = []
    plan_symbols, seen_symbols = planned.get("symbols", {}), seen.get("symbols", {})
    missing = sorted(set(plan_symbols) - set(seen_symbols))
    if missing:
        found.append(Violation("API_MISSING", f"the interface declares {', '.join(missing)}, the file lacks them", rel, rel))
    for name in sorted(set(plan_symbols) & set(seen_symbols)):
        want, got = plan_symbols[name], seen_symbols[name]
        if want["kind"] != got["kind"]:
            found.append(Violation("API_KIND", f"{name} must be a {want['kind']}, it is a {got['kind']}", rel, rel))
        elif want.get("params") is not None and not _compatible(want, got):
            found.append(Violation(
                "API_SIGNATURE",
                f"{name}({', '.join(got['params'])}) breaks the interface ({', '.join(want['params'])}): keep the planned "
                "parameters in their order; a parameter you add needs a default",
                rel, rel,
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
        if is_module and rel not in edge.members and f"I:{rel}" in h.edges and h.would_cycle(edge.id, f"I:{rel}"):
            found.append(Violation("IMPORT_CYCLE", f"imports {producer}, which already depends on {rel}", rel, rel))
    return found


def _test_diff(rel: str, seen: dict[str, Any], h: Hypergraph) -> list[Violation]:
    outside = sorted({
        f"{cls}.{attr}"
        for producer, cls, attr in seen.get("attrs_used", [])
        # only objects of a planned class: the result of a function (`mask = make_mask(); mask.shape`) is no API of
        # the plan (2026-11-21, 02: `get_ground_truth_mask.shape` rejected the tester four times)
        if f"I:{producer}" in h.edges and h.edges[f"I:{producer}"].spec.get("symbols", {}).get(cls, {}).get("kind") == "class"
        and f"{cls}.{attr}" not in h.edges[f"I:{producer}"].spec.get("symbols", {})
    })
    if not outside:
        return []
    return [Violation(
        "TEST_OUTSIDE_SPEC", f"reads {', '.join(outside)}, which the interface does not declare (test only declared methods and attributes)", rel, rel
    )]


def planned_module_for_test(h: Hypergraph, rel: str) -> str | None:
    """The planned module an unplanned test file tests: `tests/test_<stem>.py` for a module named `<stem>.py`."""
    stem = Path(rel).stem.removeprefix("test_").removesuffix("_test")
    return next((e.id.removeprefix("I:") for e in h.edges.values() if e.type == "I" and Path(e.id).stem == stem), None)


def helper_importers(h: Hypergraph, observed: dict[str, dict[str, Any] | None], rel: str) -> list[str]:
    """Planned code vertices whose file (or helper file) imports `rel`."""
    importers = []
    for vertex in h.vertices.values():
        if vertex.kind not in ("code", "entry"):
            continue
        if any(rel in ((observed.get(f) or {}).get("uses") or {}) for f in h.files_of(vertex.id)):
            importers.append(vertex.id)
    return sorted(importers)


def diff(h: Hypergraph, observed: dict[str, dict[str, Any] | None]) -> list[Violation]:
    """H_obs − H: broken promises of the plan (see the module docstring); additions are not violations."""
    found: list[Violation] = []
    for rel, seen in observed.items():
        vertex = h.vertices.get(rel)
        if vertex is None:
            if Path(rel).name == "__init__.py" or h.owner_of(rel) is not None:
                continue
            if _is_test(rel) and planned_module_for_test(h, rel):
                found += _test_diff(rel, seen or {}, h) + _import_diff(rel, seen or {}, h, False)
                continue
            if not _is_test(rel) and helper_importers(h, observed, rel):
                continue
            found.append(Violation(
                "FILE_OUTSIDE_PLAN",
                "no planned artefact has this path and no planned module imports it: put the helper in the module "
                "it serves (a private `_name`), or import it from that module in the same answer",
                rel, rel,
            ))
            continue
        if seen is None:
            continue
        if vertex.kind in ("code", "entry"):
            found += _module_diff(rel, h.edges[f"I:{rel}"].spec, seen)
        found += _import_diff(rel, seen, h, vertex.kind in ("code", "entry"))
        found += _test_diff(rel, seen, h)
    return found


def absorbable(h: Hypergraph, observed: dict[str, dict[str, Any] | None], paths: set[str]) -> dict[str, list[Any]]:
    """What the files in `paths` add to H without breaking it: helper files, tests of planned modules, imports of
    planned modules the plan did not foresee. The orchestrator records them (`SpecGateMixin._absorb`)."""
    helpers: list[tuple[str, str]] = []
    tests: list[tuple[str, str]] = []
    uses: list[tuple[str, str]] = []
    for rel in sorted(paths):
        if rel not in observed or Path(rel).name == "__init__.py":
            continue
        if rel not in h.vertices and h.owner_of(rel) is None:
            if _is_test(rel):
                module = planned_module_for_test(h, rel)
                if module:
                    tests.append((rel, module))
            else:
                owners = helper_importers(h, observed, rel)
                if owners:
                    helpers.append((rel, owners[0]))
        vertex = h.vertices.get(rel)
        if vertex is not None and vertex.kind in ("code", "entry") and observed.get(rel):
            for producer in (observed[rel] or {}).get("uses", {}):
                edge = h.edges.get(f"I:{producer}")
                if edge is not None and rel not in edge.members and not h.would_cycle(edge.id, f"I:{rel}"):
                    uses.append((rel, producer))
    return {"helpers": helpers, "tests": tests, "uses": uses}
