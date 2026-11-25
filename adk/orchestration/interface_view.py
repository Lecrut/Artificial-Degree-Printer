"""What an agent reads of a planned interface: the annotations, the return types and the docstrings that σ
(names and parameters only) does not carry.

2026-11-23: `seed_tester` was told to take expected values from the docstrings of the interface, but saw only names
and parameters (01: a test asserted `q_table` is an `np.ndarray`, the interface says `dict`; 02: `len(predict(X))`
against a declared tuple). `seed_coder` called the modules it uses without their types (`env.step` guessed as a
3-tuple, a board passed as a list where a tuple was declared)."""

from __future__ import annotations

import ast
import re

from adk.tools.verification.contract_check import stub_source

_RAISE_STUB = re.compile(r"^(\s*)raise NotImplementedError\s*$", re.M)

FULL_CHARS = 6000  # the interface of the module under test
USED_CHARS = 3000  # what one module takes from another
TOTAL_CHARS = 9000  # everything a coder reads of the modules it uses


def interface_view(source: str) -> str:
    """What a planning critic or an agent reads of an interface: every body as `...` (the prompts say so). The stub the
    harness imports has `raise NotImplementedError`, and a critic that saw it asked for the body to be implemented
    (2026-11-22, 01: "plots.py:plot_results raises NotImplementedError instead of generating the charts"). A module
    that already exists keeps its bodies in `existing`; this is what stops them reaching a tester or an author."""
    return _RAISE_STUB.sub(r"\1...", stub_source(source) or source)


def _top_name(node: ast.stmt) -> str | None:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return node.name
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        return node.targets[0].id
    return None


def used_part(source: str, names: list[str]) -> str:
    """The top-level definitions of an interface source that `names` pick (a class with all its methods and
    docstrings); the whole source when no name is given or none matches. Cut at `USED_CHARS`."""
    wanted = {n for n in names if n != "*"}
    source = interface_view(source)
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source[:USED_CHARS]
    parts = [ast.get_source_segment(source, node) or "" for node in tree.body if _top_name(node) in wanted]
    return ("\n\n".join(p for p in parts if p) if parts else source)[:USED_CHARS]


def interface_for_test(interfaces: dict[str, str], module: str | None) -> str:
    """The full planned interface of the module a test is for."""
    return interface_view(str(interfaces.get(module or "") or ""))[:FULL_CHARS]


def interfaces_for_coder(interfaces: dict[str, str], uses: dict[str, list[str]]) -> dict[str, str]:
    """`module -> the used part of its planned interface` for every module a coder's module uses, within a total budget."""
    out: dict[str, str] = {}
    left = TOTAL_CHARS
    for module in sorted(uses):
        source = interfaces.get(module)
        if not source or left <= 0:
            continue
        part = used_part(str(source), list(uses[module]))[:left]
        out[module] = part
        left -= len(part)
    return out


def labelled(interfaces: dict[str, str], modules: list[str]) -> str:
    """Full interfaces of the given modules, each under its file name (for a test review)."""
    return "\n\n".join(f"# {m}\n{interface_view(str(interfaces[m]))[:FULL_CHARS]}" for m in dict.fromkeys(modules) if interfaces.get(m))
