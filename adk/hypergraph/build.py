"""H from the plan: σ of every module parsed from the plan's interface source, and the full hypergraph (Audit VI
§VII.12.5–§VII.12.6). The validation of the plan's code before any code exists is in `validate.py`."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

from adk.hypergraph.model import Edge, Hypergraph, Vertex, Violation, check_invariants, module_import_path

_RESEARCH_AGENTS = {"background_researcher", "discoverer_researcher", "sota_researcher"}
RESULTS_WORDS = re.compile(r"wynik|eksperyment|ewaluac|dyskusj|wniosk|result|experiment|evaluat|discussion|conclusion", re.I)
RESULTS_FILE = "results.csv"
BIB_FILE = "references.bib"


def _params(args: ast.arguments) -> tuple[list[str], list[str]]:
    """(all parameter names, the required ones) — `self`/`cls` excluded from the required list."""
    positional = args.posonlyargs + args.args
    names = [a.arg for a in positional] + [a.arg for a in args.kwonlyargs]
    first_default = len(positional) - len(args.defaults)
    required = [a.arg for i, a in enumerate(positional) if i < first_default and a.arg not in ("self", "cls")]
    required += [a.arg for a, d in zip(args.kwonlyargs, args.kw_defaults) if d is None]
    return names, required


def _public_attributes(cls: ast.ClassDef) -> list[str]:
    """Public data attributes of a class: annotated or assigned in the class body, or `self.x = …` in a method.
    The interface declares the ones tests may read (`mean_: float`); undeclared ones are internal state."""
    found: list[str] = []
    for item in cls.body:
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            found.append(item.target.id)
        elif isinstance(item, ast.Assign):
            found += [t.id for t in item.targets if isinstance(t, ast.Name)]
        elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for node in ast.walk(item):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
                found += [
                    t.attr for t in targets
                    if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self"
                ]
    return [a for a in dict.fromkeys(found) if not a.startswith("_")]


def resolve_import(importer: str, module: str | None, level: int, modules: dict[str, str]) -> str | None:
    """Planned module an import refers to (`modules`: dotted path -> rel)."""
    if level:
        base = module_import_path(importer).split(".")[:-level]
        dotted = ".".join([*base, *(module.split(".") if module else [])])
    else:
        dotted = module or ""
    return modules.get(dotted)


def spec_from_stub(rel: str, source: str, modules: dict[str, str]) -> dict[str, Any]:
    """σ(I:rel): public symbols (constants with their type, functions and methods with parameters), what the
    module uses from other planned modules, third-party packages it imports. Behaviour is described in the docstrings
    in words; the plan carries no executable examples (2026-11-22)."""
    tree = ast.parse(source)
    symbols: dict[str, dict[str, Any]] = {}
    uses: dict[str, list[str]] = {}
    packages: set[str] = set()
    module_aliases: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            target = resolve_import(rel, node.module, node.level, modules)
            if target:
                uses.setdefault(target, []).extend(a.name for a in node.names)
            elif not node.level and node.module:
                packages.add(node.module.split(".")[0])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                target = modules.get(alias.name)
                if target:
                    uses.setdefault(target, [])
                    if alias.asname or "." not in alias.name:
                        module_aliases[alias.asname or alias.name] = target
                else:
                    packages.add(alias.name.split(".")[0])
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and not node.target.id.startswith("_"):
            symbols[node.target.id] = {"kind": "const", "type": ast.unparse(node.annotation)}
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and not t.id.startswith("_"):
                    symbols[t.id] = {"kind": "const", "type": None}
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            names, required = _params(node.args)
            symbols[node.name] = {"kind": "func", "params": names, "required": required}
        elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            symbols[node.name] = {"kind": "class"}
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
                    item.name == "__init__" or not item.name.startswith("_")
                ):
                    names, required = _params(item.args)
                    symbols[f"{node.name}.{item.name}"] = {"kind": "method", "params": names, "required": required}
            for attr in _public_attributes(node):
                symbols.setdefault(f"{node.name}.{attr}", {"kind": "attr"})
    # `import core` + `core.is_terminal(...)` uses `is_terminal` as much as `from core import is_terminal` does.
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load)
            and isinstance(node.value, ast.Name) and node.value.id in module_aliases
        ):
            uses[module_aliases[node.value.id]].append(node.attr)
    return {
        "import": module_import_path(rel),
        "symbols": symbols,
        "uses": {k: sorted(set(v)) for k, v in uses.items()},
        "packages": sorted(packages),
    }


def _test_target(rel: str) -> str:
    rel = rel.replace("\\", "/")
    return rel if "/" in rel else f"tests/{rel}"


def build_from_plan(
    interfaces: dict[str, str],
    entrypoint: str | None,
    tasks: list[dict[str, Any]],
    chapters: list[dict[str, Any]],
    metrics: list[str],
    plots: str | None = None,
) -> tuple[Hypergraph, list[Violation]]:
    """The full H (§VII.12.6). Call after `code_violations` passed; what still breaks an invariant is returned."""
    modules = {module_import_path(rel): rel for rel in interfaces}
    specs = {rel: spec_from_stub(rel, src, modules) for rel, src in interfaces.items()}
    entry_file = (entrypoint or "").partition(":")[0]
    descriptions: dict[str, str] = {}
    for t in tasks:
        if isinstance(t, dict):
            descriptions.setdefault(str(t.get("target_node", "")).replace("\\", "/"), str(t.get("description", "")))

    vertices: dict[str, Vertex] = {}
    edges: dict[str, Edge] = {}
    order: list[tuple[str, str]] = []
    for rel, spec in specs.items():
        kind = "entry" if rel == entry_file else "code"
        vertices[rel] = Vertex(rel, kind, "coder", "stub", descriptions.get(rel, ""))
        edges[f"I:{rel}"] = Edge(f"I:{rel}", "I", {rel: "P"}, spec)
    for rel, spec in specs.items():
        for producer in spec["uses"]:
            edges[f"I:{producer}"].members.setdefault(rel, "C")
            order.append((f"I:{producer}", f"I:{rel}"))

    dropped: list[Violation] = []
    for t in tasks:
        target = str(t.get("target_node", "")) if isinstance(t, dict) else ""
        name = Path(target).name
        if not (name.startswith("test_") and name.endswith(".py")):
            continue
        test = _test_target(target)
        stem = name.removeprefix("test_").removesuffix(".py")
        module = next((m for m in specs if Path(m).stem == stem), None) or next(
            (m for m in specs if Path(m).stem in stem), None
        )
        if module is None:
            dropped.append(Violation("TEST_WITHOUT_MODULE", f"{test} tests no planned module", test))
            continue
        vertices.setdefault(test, Vertex(test, "test", "tester", "spec", str(t.get("description", ""))))
        edges[f"I:{module}"].members[test] = "T"

    research = sorted({
        str(t.get("target_node", "")).replace("\\", "/")
        for t in tasks
        if isinstance(t, dict) and t.get("assigned_agent") in _RESEARCH_AGENTS and str(t.get("target_node", "")).endswith(".md")
        and not str(t.get("target_node", "")).endswith("thesis.md")
    })
    for rel in research:
        vertices[rel] = Vertex(rel, "research", "researcher", "spec", descriptions.get(rel, ""))

    if entry_file in specs:
        vertices[RESULTS_FILE] = Vertex(RESULTS_FILE, "data", None, "spec")
        members = {entry_file: "P", RESULTS_FILE: "O"}
        plots_file = (plots or "").partition(":")[0]
        if plots_file in specs:
            members[plots_file] = "C"
        edges["R:run"] = Edge(
            "R:run", "R", members,
            {"entry": entrypoint, "metrics": list(metrics or []), "plots": plots if plots_file in specs else ""},
        )
        closure, frontier = set(), [entry_file]
        while frontier:
            current = frontier.pop()
            for producer in specs.get(current, {}).get("uses", {}):
                if producer not in closure:
                    closure.add(producer)
                    frontier.append(producer)
        # Every module the experiment runs is a member of R: a change to any of them makes the results stale
        # (2026-11-17: only the entrypoint was hashed, so a change of the method left old results "fresh").
        for module in sorted(closure - {entry_file}):
            members.setdefault(module, "C")
        order += [(f"I:{m}", "R:run") for m in sorted(closure | {entry_file})]

    if chapters:
        vertices[BIB_FILE] = Vertex(BIB_FILE, "bib", "writer", "spec")
    for i, ch in enumerate(chapters, 1):
        index = int(ch.get("index") or i) if isinstance(ch, dict) else i
        title = str(ch.get("title", "")) if isinstance(ch, dict) else str(ch)
        focus = str(ch.get("focus", "")) if isinstance(ch, dict) else ""
        uses_results = bool(ch.get("uses_results")) if isinstance(ch, dict) and "uses_results" in ch else bool(
            RESULTS_WORDS.search(f"{title} {focus}")
        )
        cid = f"thesis.md#ch{index}"
        vertices[cid] = Vertex(cid, "chapter", "writer", "spec", f"{title} — {focus}".strip(" —"))
        members = {cid: "X", BIB_FILE: "C", **{r: "C" for r in research}}
        if uses_results and "R:run" in edges:
            members[RESULTS_FILE] = "C"
            order.append(("R:run", f"N:{cid}"))
        edges[f"N:{cid}"] = Edge(f"N:{cid}", "N", members, {"title": title, "focus": focus, "uses_results": uses_results})

    h = Hypergraph(vertices, edges, sorted(set(order)))
    return h, dropped + check_invariants(h)
