"""H from the plan: σ of every module parsed from the plan's interface source, validation of the code part of the
plan before any code exists, and the full hypergraph (Audit VI §VII.12.5–§VII.12.6)."""

from __future__ import annotations

import ast
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from adk.hypergraph.model import Edge, Hypergraph, Vertex, Violation, check_invariants
from adk.tools.building.import_sync import module_import_path
from adk.tools.verification.contract_check import stub_source

_RESEARCH_AGENTS = {"background_researcher", "discoverer_researcher", "sota_researcher"}
_RESULTS_WORDS = re.compile(r"wynik|eksperyment|ewaluac|dyskusj|wniosk|result|experiment|evaluat|discussion|conclusion", re.I)
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
    module uses from other planned modules, third-party packages it imports, doctest examples (behaviour)."""
    tree = ast.parse(source)
    symbols: dict[str, dict[str, Any]] = {}
    uses: dict[str, list[str]] = {}
    packages: set[str] = set()
    behaviour: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            doc = ast.get_docstring(node)
            if doc and ">>>" in doc:
                behaviour.append(doc)
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
    return {
        "import": module_import_path(rel),
        "symbols": symbols,
        "uses": {k: sorted(set(v)) for k, v in uses.items()},
        "packages": sorted(packages),
        "behaviour": behaviour,
    }


_IMPORT_PROBE = r"""
import importlib, json, sys, traceback, typing
root, plan = sys.argv[1], json.loads(sys.argv[2])
sys.path.insert(0, root)
out = {}
_SIMPLE = {"list": list, "dict": dict, "tuple": tuple, "set": set, "int": int, "float": (int, float), "str": str, "bool": bool}
for rel, (dotted, consts) in plan.items():
    try:
        mod = importlib.import_module(dotted)
    except BaseException as exc:
        frames = [f.filename for f in traceback.extract_tb(exc.__traceback__) if f.filename.startswith(root)]
        origin = getattr(exc, "filename", None) if isinstance(exc, SyntaxError) else (frames[-1] if frames else None)
        out[rel] = {"error": f"{type(exc).__name__}: {exc}", "origin": origin}
        continue
    bad = []
    for name, declared in consts.items():
        expected = _SIMPLE.get((declared or "").split("[")[0].strip())
        if expected and not isinstance(getattr(mod, name, None), expected):
            bad.append(f"{name}: declared {declared}, value is {type(getattr(mod, name, None)).__name__}")
    out[rel] = {"const_mismatch": bad}
print(json.dumps(out))
"""


def _stub_problems(specs: dict[str, dict[str, Any]], interfaces: dict[str, str]) -> list[Violation]:
    """Import every stub in a scratch directory: a plan whose interfaces do not even import (a name used without
    its import, a broken constant) used to become the skeleton and fail for an hour (Audit VI X2)."""
    found: list[Violation] = []
    with tempfile.TemporaryDirectory(prefix="adk_stub_probe_") as tmp:
        root = Path(tmp).resolve()
        for rel, source in interfaces.items():
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(stub_source(source) or source, encoding="utf-8")
        plan = {
            rel: (spec["import"], {n: s.get("type") for n, s in spec["symbols"].items() if s["kind"] == "const"})
            for rel, spec in specs.items()
        }
        proc = subprocess.run(
            [sys.executable, "-c", _IMPORT_PROBE, str(root), json.dumps(plan)],
            capture_output=True, text=True, timeout=120, cwd=str(root),
        )
        try:
            results = json.loads(proc.stdout.strip().splitlines()[-1])
        except (IndexError, json.JSONDecodeError):
            return [Violation("STUB_PROBE_FAILED", (proc.stderr or proc.stdout)[-400:])]
        for rel, res in results.items():
            if res.get("error"):
                origin = res.get("origin")
                culprit = Path(origin).resolve().relative_to(root).as_posix() if origin and str(origin).startswith(str(root)) else rel
                found.append(Violation("STUB_DOES_NOT_IMPORT", res["error"], rel, culprit))
            for mismatch in res.get("const_mismatch", []):
                found.append(Violation("CONSTANT_TYPE_MISMATCH", mismatch, rel, rel))
    # A failure inside one module is reported once, at the module where it happens.
    unique: dict[tuple[str, str | None], Violation] = {}
    for v in found:
        unique.setdefault((v.detail, v.culprit), v)
    return list(unique.values())


def _package_available(top: str) -> bool:
    if top in sys.stdlib_module_names:
        return True
    try:
        return importlib.util.find_spec(top) is not None
    except (ImportError, ValueError):
        return False


def code_violations(interfaces: dict[str, str], entrypoint: str | None) -> tuple[dict[str, dict[str, Any]], list[Violation]]:
    """σ of every planned module and every reason the code part of the plan cannot work as written
    (invariants 2–5, 7–9 of §VII.12.10)."""
    found: list[Violation] = []
    modules = {module_import_path(rel): rel for rel in interfaces}
    stems: dict[str, list[str]] = {}
    for rel in interfaces:
        stems.setdefault(Path(rel).stem, []).append(rel)
    for stem, rels in stems.items():
        if len(rels) > 1 and stem != "__init__":
            found.append(Violation("DUPLICATE_MODULE", f"{', '.join(sorted(rels))} play the same role; keep one", rels[0]))
    specs: dict[str, dict[str, Any]] = {}
    for rel, source in interfaces.items():
        try:
            specs[rel] = spec_from_stub(rel, source, modules)
        except SyntaxError as exc:
            found.append(Violation("INTERFACE_DOES_NOT_PARSE", str(exc), rel, rel))
    planned_tops = {dotted.split(".")[0] for dotted in modules}
    for rel, spec in specs.items():
        for producer, names in spec["uses"].items():
            missing = [n for n in names if n not in specs.get(producer, {}).get("symbols", {}) and n != "*"]
            if missing:
                found.append(Violation("USES_UNDECLARED", f"imports {', '.join(missing)} from {producer}, whose interface does not declare them", rel, rel))
        for top in spec["packages"]:
            if top not in planned_tops and not _package_available(top):
                found.append(Violation("PACKAGE_UNAVAILABLE", f"imports `{top}`, which is neither a planned module nor installed", rel, rel))
    entry_file, _, entry_func = (entrypoint or "").partition(":")
    if specs and not entry_file:
        found.append(Violation("NO_ENTRYPOINT", "the plan declares no experiment entrypoint (path.py:function)"))
    elif entry_file and entry_file not in specs:
        found.append(Violation("ENTRYPOINT_NOT_PLANNED", f"{entry_file} has no interface in the plan", entry_file))
    elif entry_file:
        func = specs[entry_file]["symbols"].get(entry_func or "")
        if not func or func["kind"] != "func":
            found.append(Violation("ENTRYPOINT_NOT_DECLARED", f"{entry_file} declares no function `{entry_func}`", entry_file, entry_file))
        elif func["required"]:
            found.append(Violation(
                "ENTRYPOINT_HAS_ARGUMENTS",
                f"{entry_func}({', '.join(func['required'])}): the harness calls the entrypoint without arguments; "
                "read configuration inside the function",
                entry_file, entry_file,
            ))
    if specs and not any(v.rule in ("INTERFACE_DOES_NOT_PARSE", "DUPLICATE_MODULE") for v in found):
        found += _stub_problems(specs, interfaces)
    return specs, found


def _test_target(rel: str) -> str:
    rel = rel.replace("\\", "/")
    return rel if "/" in rel else f"tests/{rel}"


def build_from_plan(
    interfaces: dict[str, str],
    entrypoint: str | None,
    tasks: list[dict[str, Any]],
    chapters: list[dict[str, Any]],
    metrics: list[str],
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
        for rel, spec in specs.items():
            if "generate_plots" in spec["symbols"]:
                members[rel] = "C"
        edges["R:run"] = Edge("R:run", "R", members, {"entry": entrypoint, "metrics": list(metrics or [])})
        closure, frontier = set(), [entry_file]
        while frontier:
            current = frontier.pop()
            for producer in specs.get(current, {}).get("uses", {}):
                if producer not in closure:
                    closure.add(producer)
                    frontier.append(producer)
        order += [(f"I:{m}", "R:run") for m in sorted(closure | {entry_file})]

    if chapters:
        vertices[BIB_FILE] = Vertex(BIB_FILE, "bib", "writer", "spec")
    for i, ch in enumerate(chapters, 1):
        index = int(ch.get("index") or i) if isinstance(ch, dict) else i
        title = str(ch.get("title", "")) if isinstance(ch, dict) else str(ch)
        focus = str(ch.get("focus", "")) if isinstance(ch, dict) else ""
        uses_results = bool(ch.get("uses_results")) if isinstance(ch, dict) and "uses_results" in ch else bool(
            _RESULTS_WORDS.search(f"{title} {focus}")
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
