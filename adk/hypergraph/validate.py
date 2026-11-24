"""Validation of the code part of a plan before any code exists (Audit VI A3, Audit VII B1-B3): the stubs of
every interface import, constants have their declared types, the entrypoint takes no arguments and runs every
planned module. Docstrings describe behaviour in words (2026-11-22: examples in the plan were unsatisfiable in 21 of
30 failed verdicts, so the plan no longer carries executable examples)."""

from __future__ import annotations

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
import importlib, json, sys, traceback
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
        try:
            proc = subprocess.run(
                [sys.executable, "-c", _IMPORT_PROBE, str(root), json.dumps(plan)],
                capture_output=True, text=True, timeout=120, cwd=str(root),
            )
        except subprocess.TimeoutExpired:
            return [Violation("STUB_PROBE_TIMEOUT", "importing the stubs took over 120 s")]
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


def _unused_by_entrypoint(specs: dict[str, dict[str, Any]], entry_file: str, plots_file: str = "") -> list[str]:
    """Planned code modules the experiment never imports (top level, transitively). 2026-11-17: the entrypoint in
    config.py imported nothing, the coder rewrote the game inside it, and the planned method never ran (83x)."""
    reached, frontier = {entry_file}, [entry_file]
    while frontier:
        for producer in specs.get(frontier.pop(), {}).get("uses", {}):
            if producer not in reached:
                reached.add(producer)
                frontier.append(producer)
    # The declared `plots` function is called by the harness after the experiment, not by the entrypoint.
    return sorted(rel for rel in specs if rel not in reached and rel != plots_file and Path(rel).name != "__init__.py")


def _declared_call(specs: dict[str, dict[str, Any]], declared: str, role: str) -> list[Violation]:
    """A `path.py:function` the harness calls without arguments (the entrypoint, the declared `plots`)."""
    file, _, func_name = declared.partition(":")
    if file not in specs:
        return [Violation(f"{role}_NOT_PLANNED", f"{file} has no interface in the plan", file)]
    func = specs[file]["symbols"].get(func_name or "")
    if not func or func["kind"] != "func":
        return [Violation(f"{role}_NOT_DECLARED", f"{file} declares no function `{func_name}`", file, file)]
    if func["required"]:
        return [Violation(
            f"{role}_HAS_ARGUMENTS",
            f"{func_name}({', '.join(func['required'])}): the harness calls it without arguments; "
            "read configuration inside the function",
            file, file,
        )]
    return []


def code_violations(
    interfaces: dict[str, str], entrypoint: str | None, plots: str | None = None, metrics: list[str] | None = None
) -> tuple[dict[str, dict[str, Any]], list[Violation]]:
    """σ of every planned module and every reason the code part of the plan cannot work as written
    (invariants 2–5, 7–9 of §VII.12.10). `plots` is the optional declared figures function (§XIII F2); `metrics`
    the declared metrics, each of which the entrypoint's interface has to name (the plan delivers the data it promises)."""
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
    elif entry_file:
        found += _declared_call(specs, f"{entry_file}:{entry_func}", "ENTRYPOINT")
    if entry_file in interfaces:
        text = interfaces[entry_file].lower()
        found += [Violation(
            "METRIC_NOT_IN_ENTRYPOINT",
            f"the declared metric `{m}` is not named in the interface of {entry_file}: its docstring must say which "
            f"`results.csv` row (method, `{m}`) the experiment writes",
            entry_file, entry_file,
        ) for m in metrics or [] if str(m).strip().lower() not in text]
    plots_file = (plots or "").partition(":")[0]
    if plots_file:
        found += _declared_call(specs, str(plots), "PLOTS")
    if entry_file in specs:
        # One finding per module: a patch that imports four of five is progress (2026-11-21, 02: one finding listing
        # all five changed its text, counted as "1 fixed, 1 new", and the better patch was rejected).
        found += [Violation(
            "ENTRYPOINT_DOES_NOT_USE",
            f"{entry_file} never imports {module} (directly or through other modules, at module top level): the "
            "experiment must run the planned method and baseline through their modules, not reimplement them",
            entry_file, entry_file,
        ) for module in _unused_by_entrypoint(specs, entry_file, plots_file)]
    if specs and not any(v.rule in ("INTERFACE_DOES_NOT_PARSE", "DUPLICATE_MODULE") for v in found):
        found += _stub_problems(specs, interfaces)
    return specs, found
