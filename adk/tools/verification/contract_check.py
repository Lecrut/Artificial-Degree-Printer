"""Hyperedge contract gate: test files may only use symbols that their coupled workspace modules define."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from adk.core.models import read_json_state, resolve_adk_path

_NESTED_BODIES = ("body", "orelse", "finalbody", "handlers")


def _module_names(tree: ast.Module) -> set[str] | None:
    """Top-level names a module defines (incl. imports and if/try branches); None if dynamic (`__getattr__`/`*`)."""
    names: set[str] = set()
    stack: list[ast.stmt] = list(tree.body)
    while stack:
        node = stack.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name == "__getattr__":
                return None
            names.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                if alias.name == "*":
                    return None
                names.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                for sub in ast.walk(target):
                    if isinstance(sub, ast.Name):
                        names.add(sub.id)
        else:
            for field in _NESTED_BODIES:
                stack.extend(getattr(node, field, None) or [])
    return names


def _used_symbols(tree: ast.Module, module_stem: str) -> set[str]:
    """Symbols a test reads from `module_stem` via `import m [as a]` + `a.X` or `from m import X`."""
    aliases: set[str] = set()
    used: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[-1] == module_stem:
                    aliases.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[-1] == module_stem:
            used.update(alias.name for alias in node.names if alias.name != "*")
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.ctx, ast.Load)
            and isinstance(node.value, ast.Name)
            and node.value.id in aliases
        ):
            used.add(node.attr)
    return used


def _parse(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, ValueError):
        return None


def _numeric_defaults(func: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """Parameters whose default is a literal int/float (bools are flags, not experiment knobs)."""
    args = func.args
    positional = args.posonlyargs + args.args
    pairs = list(zip(positional[len(positional) - len(args.defaults):], args.defaults))
    pairs += [(a, d) for a, d in zip(args.kwonlyargs, args.kw_defaults) if d is not None]
    return [
        f"{a.arg}={d.value!r}"
        for a, d in pairs
        if isinstance(d, ast.Constant) and isinstance(d.value, (int, float)) and not isinstance(d.value, bool)
    ]


def check_entrypoint_parameters(workspace_dir: str | Path, entrypoint: str | None) -> list[str]:
    """The experiment entrypoint is called without arguments, so a literal numeric default IS the experiment
    setting. It must be a configuration symbol instead, or the thesis cannot point at it."""
    if not entrypoint:
        return []
    file_part, _, func_name = entrypoint.partition(":")
    tree = _parse(resolve_adk_path(workspace_dir) / file_part)
    if tree is None:
        return []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == (func_name or "main"):
            hidden = _numeric_defaults(node)
            if hidden:
                return [
                    f"Naruszenie kontraktu parametrów: punkt wejścia {entrypoint} ma liczbowe wartości domyślne "
                    f"({', '.join(hidden)}). Przenieś je do pliku konfiguracyjnego jako symbole i czytaj je w funkcji."
                ]
    return []


def check_parameter_closure(workspace_dir: str | Path) -> list[str]:
    """Warnings for UPPER_CASE module constants that no workspace Python file reads (declared but unused)."""
    w_dir = resolve_adk_path(workspace_dir)
    trees: dict[str, ast.Module] = {}
    for path in sorted(w_dir.rglob("*.py")) if w_dir.exists() else []:
        rel = path.relative_to(w_dir)
        if "__pycache__" in rel.parts or rel.parts[0] in ("benchmarks", "logs", ".venv", "venv"):
            continue
        tree = _parse(path)
        if tree is not None:
            trees[rel.as_posix()] = tree
    read_names: set[str] = set()
    for tree in trees.values():
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
                read_names.add(node.attr)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                read_names.add(node.id)
            elif isinstance(node, ast.ImportFrom):
                read_names.update(alias.name for alias in node.names)
    warnings: list[str] = []
    for rel, tree in trees.items():
        for node in tree.body:
            targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
            for target in targets:
                if isinstance(target, ast.Name) and target.id.isupper() and target.id not in read_names:
                    warnings.append(f"Parametr {rel}:{target.id} jest zadeklarowany, ale żaden kod go nie używa.")
    return warnings


def check_test_contract(
    workspace_dir: str | Path = "workspace",
    matrix_path: str | Path = "state/hypergraph_matrix.json",
) -> list[str]:
    """For every hyperedge coupling a `test_*.py` node with a `.py` module node, report module symbols the
    test uses that the module does not define. Returns one message per (test, module) pair with violations."""
    w_dir = resolve_adk_path(workspace_dir)
    data: dict[str, Any] = read_json_state(matrix_path)
    nodes: dict[str, Any] = data.get("nodes", {})
    pairs: set[tuple[str, str]] = set()
    for members in data.get("edges", {}).values():
        paths = [str(nodes.get(m, {}).get("path", "")) for m in members]
        py_paths = [p for p in paths if p.endswith(".py")]
        for test_path in py_paths:
            if Path(test_path).name.startswith("test_"):
                pairs.update(
                    (test_path, mod) for mod in py_paths if mod != test_path and not Path(mod).name.startswith("test_")
                )

    violations: list[str] = []
    for test_path, module_path in sorted(pairs):
        test_tree = _parse(w_dir / test_path)
        module_tree = _parse(w_dir / module_path)
        if test_tree is None or module_tree is None:
            continue  # missing or unparsable files are reported by py_compile/pytest
        defined = _module_names(module_tree)
        if defined is None:
            continue
        stem = Path(module_path).stem
        missing = sorted(_used_symbols(test_tree, stem) - defined)
        if missing:
            available = sorted(n for n in defined if not n.startswith("_"))
            violations.append(
                f"Naruszenie kontraktu hiperkrawędzi: {test_path} używa {', '.join(f'{stem}.{m}' for m in missing)}, "
                f"których nie ma w {module_path}. Dostępne w {module_path}: {', '.join(available) or '(brak)'}."
            )
    return violations
