"""Validation of the code part of a plan before any code exists (Audit VI A3, Audit VII B1-B3): the stubs of
every interface import, constants have their declared types, doctests hold on the stubs, no example discards a
returned value, the entrypoint takes no arguments and runs every planned module."""

from __future__ import annotations

import ast
import doctest
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from adk.hypergraph.build import spec_from_stub
from adk.hypergraph.model import Violation, module_import_path
from adk.tools.verification.contract_check import stub_source


_IMPORT_PROBE = r"""
import contextlib, doctest, importlib, io, json, sys, traceback, typing
root, plan = sys.argv[1], json.loads(sys.argv[2])
sys.path.insert(0, root)
out = {}
_SIMPLE = {"list": list, "dict": dict, "tuple": tuple, "set": set, "int": int, "float": (int, float), "str": str, "bool": bool}
_CHECKER = doctest.OutputChecker()


def _names(source):
    import ast
    tree = ast.parse(source)
    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    bound = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del))}
    return used, bound


def doctests_on_stubs(mod):
    # Every example that does not depend on a stub's result must already hold: it does not depend on any
    # implementation (2026-11-17: `ns = (0,)*9; ns[0]=1` raised TypeError for every implementation, 16x).
    # A name bound by an example that called a stub is "pending"; examples reading it are not judged.
    bad = []
    for test in doctest.DocTestFinder(exclude_empty=True).find(mod, mod.__name__):
        globs = dict(test.globs)
        pending = set()
        for ex in test.examples:
            try:
                used, bound = _names(ex.source)
            except SyntaxError as exc:
                bad.append(f"{test.name}: `{ex.source.strip()}` is not valid Python ({exc.msg})")
                break
            if used & pending:
                pending |= bound
                continue
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    exec(compile(ex.source, "<doctest>", "single"), globs)
            except NotImplementedError:
                pending |= bound
                continue
            except BaseException as exc:
                if ex.exc_msg is None:
                    bad.append(f"{test.name}: `{ex.source.strip()}` raises {type(exc).__name__}: {exc}")
                    break
                continue
            flags = sum(flag for flag, on in ex.options.items() if on)
            if ex.exc_msg is not None or not _CHECKER.check_output(ex.want, buf.getvalue(), flags):
                got = buf.getvalue().strip() or "nothing"
                bad.append(f"{test.name}: `{ex.source.strip()}` gives {got!r}, the example expects {ex.want.strip() or ex.exc_msg!r}")
                break
    return bad


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
    out[rel] = {"const_mismatch": bad, "doctest": doctests_on_stubs(mod)}
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
        try:
            proc = subprocess.run(
                [sys.executable, "-c", _IMPORT_PROBE, str(root), json.dumps(plan)],
                capture_output=True, text=True, timeout=120, cwd=str(root),
            )
        except subprocess.TimeoutExpired:
            return [Violation("STUB_PROBE_TIMEOUT", "importing the stubs or running their doctests took over 120 s")]
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
            for problem in res.get("doctest", []):
                found.append(Violation("DOCTEST_INVALID_ON_STUBS", problem, rel, rel))
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


def _discarded_returns(interfaces: dict[str, str]) -> list[Violation]:
    """Examples that call something returning a value and expect no output: doctest prints the value, so the
    example fails for every correct implementation (2026-11-17: `>>> env.reset()` before `step`, 35x in 01).
    On the stubs the call raises NotImplementedError first, so only the declared return type can tell."""
    returns: dict[str, list[str]] = {}
    trees: dict[str, ast.Module] = {}
    for rel, source in interfaces.items():
        try:
            trees[rel] = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(trees[rel]):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name != "__init__":
                returns.setdefault(node.name, []).append(ast.unparse(node.returns) if node.returns else "")
            elif isinstance(node, ast.ClassDef):
                returns.setdefault(node.name, []).append(node.name)
    found: list[Violation] = []
    parser = doctest.DocTestParser()
    for rel, tree in trees.items():
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            doc = ast.get_docstring(node) or ""
            if ">>>" not in doc:
                continue
            try:
                examples = parser.get_examples(doc)
            except ValueError as exc:
                found.append(Violation("DOCTEST_MALFORMED", str(exc), rel, rel))
                continue
            for ex in examples:
                if ex.want or ex.exc_msg is not None:
                    continue
                try:
                    stmt = ast.parse(ex.source).body
                except SyntaxError:
                    continue
                if len(stmt) != 1 or not isinstance(stmt[0], ast.Expr) or not isinstance(stmt[0].value, ast.Call):
                    continue
                func = stmt[0].value.func
                name = func.attr if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else ""
                declared = returns.get(name, [])
                if declared and all(r and r != "None" for r in declared):
                    found.append(Violation(
                        "DOCTEST_DISCARDS_RETURN",
                        f"`{ex.source.strip()}` returns {declared[0]}, so doctest prints it, but the example expects "
                        "no output: write `_ = ...` or the expected value",
                        rel, rel,
                    ))
    return found


def _unused_by_entrypoint(specs: dict[str, dict[str, Any]], entry_file: str) -> list[str]:
    """Planned code modules the experiment never imports (top level, transitively). 2026-11-17: the entrypoint in
    config.py imported nothing, the coder rewrote the game inside it, and the planned method never ran (83x)."""
    reached, frontier = {entry_file}, [entry_file]
    while frontier:
        for producer in specs.get(frontier.pop(), {}).get("uses", {}):
            if producer not in reached:
                reached.add(producer)
                frontier.append(producer)
    # `generate_plots` is called by the harness after the experiment, not by the entrypoint.
    return sorted(
        rel for rel, spec in specs.items()
        if rel not in reached and "generate_plots" not in spec["symbols"] and Path(rel).name != "__init__.py"
    )


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
        if unused := _unused_by_entrypoint(specs, entry_file):
            found.append(Violation(
                "ENTRYPOINT_DOES_NOT_USE",
                f"{entry_file} never imports {', '.join(unused)} (directly or through other modules, at module top "
                "level): the experiment must run the planned method and baseline through their modules, not "
                "reimplement them",
                entry_file, entry_file,
            ))
    found += _discarded_returns(interfaces)
    if specs and not any(v.rule in ("INTERFACE_DOES_NOT_PARSE", "DUPLICATE_MODULE") for v in found):
        found += _stub_problems(specs, interfaces)
    return specs, found
