"""Hyperedge contract gate: test files may only use symbols that their coupled workspace modules define."""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

from adk.core.models import resolve_adk_path

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
                    f"Parameter contract violation: the entrypoint {entrypoint} has numeric default values "
                    f"({', '.join(hidden)}). Move them to the configuration module as symbols and read them in the function."
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
                    warnings.append(f"Parameter {rel}:{target.id} is declared but no code uses it.")
    return warnings


def _param_names(args: ast.arguments) -> list[str]:
    """Parameter names in order; `*args`/`**kw` keep their stars. Annotations and defaults are not the interface."""
    names = [a.arg for a in args.posonlyargs + args.args]
    if args.vararg:
        names.append(f"*{args.vararg.arg}")
    names += [a.arg for a in args.kwonlyargs]
    if args.kwarg:
        names.append(f"**{args.kwarg.arg}")
    return names


def public_api(source: str) -> dict[str, list[str]] | None:
    """Public interface of a module: `func` / `Class` / `Class.method` (public and `__init__`) -> parameter names.
    None when the source does not parse (syntax errors are reported by the test runner)."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return None
    api: dict[str, list[str]] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            api[node.name] = _param_names(node.args)
        elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            api[node.name] = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
                    item.name == "__init__" or not item.name.startswith("_")
                ):
                    api[f"{node.name}.{item.name}"] = _param_names(item.args)
    return api


_STUB_KEPT = (ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def _stub_body(func: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
    doc = ast.get_docstring(func, clean=False)
    func.body = ([ast.Expr(ast.Constant(doc))] if doc is not None else []) + [
        ast.Raise(exc=ast.Name("NotImplementedError", ast.Load()), cause=None)
    ]


def _instance_attributes(cls: ast.ClassDef) -> dict[str, str]:
    """Public attributes a class assigns only through `self.x = ...` in its methods -> their annotation as text."""
    in_body = {
        t.id
        for item in cls.body
        for t in (item.targets if isinstance(item, ast.Assign) else [item.target] if isinstance(item, ast.AnnAssign) else [])
        if isinstance(t, ast.Name)
    }
    found: dict[str, str] = {}
    for item in cls.body:
        if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for node in ast.walk(item):
            pairs = (
                [(t, None) for t in node.targets] if isinstance(node, ast.Assign)
                else [(node.target, node.annotation)] if isinstance(node, ast.AnnAssign) else []
            )
            for target, annotation in pairs:
                if (
                    isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self"
                    and not target.attr.startswith("_") and target.attr not in in_body
                ):
                    found.setdefault(target.attr, ast.unparse(annotation) if annotation is not None else "object")
    return found


def stub_source(source: str) -> str | None:
    """The interface of a module with every function and method body replaced by its docstring and
    `raise NotImplementedError` (U2, 2026-11-15: the "skeleton" of a small model had 0 such bodies and 9 half
    implementations with bugs, which then became the code every later task patched). Imports, constants and
    class attributes stay; other top-level statements are dropped. None when the source does not parse."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return None
    doc = ast.get_docstring(tree, clean=False)
    body: list[ast.stmt] = [ast.Expr(ast.Constant(doc))] if doc is not None else []
    for node in tree.body:
        if not isinstance(node, _STUB_KEPT):
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _stub_body(node)
        elif isinstance(node, ast.ClassDef):
            declared = _instance_attributes(node)
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    _stub_body(item)
            # Public `self.x = ...` would vanish with the method bodies, and σ declares it (2026-11-17: 02 crashed
            # on its own stubs, API_MISSING ZScoreBaseline.threshold). Kept as a class annotation, not evaluated.
            first = 1 if ast.get_docstring(node, clean=False) is not None else 0
            node.body[first:first] = [
                ast.AnnAssign(target=ast.Name(name, ast.Store()), annotation=ast.Constant(ann), value=None, simple=1)
                for name, ann in declared.items()
            ]
        body.append(node)
    tree.body = body
    return ast.unparse(ast.fix_missing_locations(tree)) + "\n"


def is_contract_module(rel_path: str) -> bool:
    """Modules whose public API is part of the interface contract: code, not tests."""
    name = Path(rel_path).name
    return rel_path.endswith(".py") and not name.startswith("test_") and not name.endswith("_test.py")


def _resolve_workspace_module(w_dir: Path, importer_rel: str, module: str | None, level: int) -> str | None:
    """Workspace file an import statement refers to (`src.game` -> src/game.py, `.game` inside src/ -> src/game.py,
    `game` -> the unique game.py); None for third-party modules."""
    if level:
        base = Path(importer_rel).parent
        for _ in range(level - 1):
            base = base.parent
        parts = [*base.parts, *(module.split(".") if module else [])]
    else:
        parts = (module or "").split(".")
    if not parts or not parts[0]:
        return None
    for candidate in (Path(*parts).with_suffix(".py"), Path(*parts) / "__init__.py"):
        if (w_dir / candidate).is_file():
            return candidate.as_posix()
    if not level and len(parts) == 1:
        same_stem = [p for p in w_dir.rglob(f"{parts[0]}.py") if "__pycache__" not in p.parts]
        if len(same_stem) == 1:
            return same_stem[0].relative_to(w_dir).as_posix()
    return None


def _workspace_top_names(w_dir: Path) -> set[str]:
    """Top-level names the workspace itself provides: root module stems and first-level package directories."""
    tops: set[str] = set()
    for p in w_dir.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        rel = p.relative_to(w_dir)
        tops.add(rel.parts[0] if len(rel.parts) > 1 else rel.stem)
    return tops


def _package_unavailable(top: str, tops: set[str]) -> bool:
    """True when `top` is neither a workspace name, nor stdlib, nor an installed package. The environment is
    fixed for the whole run (decision D1, 2026-11-14): a missing package is a finding for the builder, never
    a reason to install anything."""
    if not top or top in tops or top in sys.stdlib_module_names:
        return False
    try:
        return importlib.util.find_spec(top) is None
    except (ImportError, ValueError):
        return True


def check_import_contract(workspace_dir: str | Path, rel_file: str) -> list[str]:
    """Static L1 check of one file: every `from <workspace module> import name` names something that module
    defines, and every absolute import resolves to the workspace, the stdlib or an installed package. Nothing
    is executed, so a broken neighbour cannot fail this file and a wrong name (`TicTacToe` for `TicTacToeGame`)
    is caught before any test runs. Unparsable neighbours are the neighbour's problem."""
    w_dir = resolve_adk_path(workspace_dir)
    tree = _parse(w_dir / rel_file)
    if tree is None:
        return []
    tops = _workspace_top_names(w_dir)
    violations: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if _package_unavailable(top, tops):
                    violations.append(
                        f"Environment contract violation: {rel_file} imports the package '{top}', which the "
                        "environment does not have. The environment is fixed for the whole run: use the packages in "
                        "'available_packages' or the project's modules (their import paths are in 'specification')."
                    )
            continue
        if not isinstance(node, ast.ImportFrom):
            continue
        if not node.level and _package_unavailable((node.module or "").split(".")[0], tops):
            violations.append(
                f"Environment contract violation: {rel_file} imports the package '{(node.module or '').split('.')[0]}', "
                "which the environment does not have. The environment is fixed for the whole run: use the packages in "
                "'available_packages' or the project's modules (their import paths are in 'specification')."
            )
            continue
        target = _resolve_workspace_module(w_dir, rel_file, node.module, node.level)
        if target is None or target == rel_file:
            continue
        target_tree = _parse(w_dir / target)
        defined = _module_names(target_tree) if target_tree is not None else None
        if defined is None:
            continue
        package_dir = Path(target).parent if Path(target).name == "__init__.py" else None
        missing = [
            alias.name
            for alias in node.names
            if alias.name != "*"
            and alias.name not in defined
            and not (package_dir is not None and (w_dir / package_dir / f"{alias.name}.py").is_file())
        ]
        if missing:
            available = sorted(n for n in defined if not n.startswith("_"))
            violations.append(
                f"Import contract violation: {rel_file} imports {', '.join(missing)} from {target}, "
                f"which that module does not define. Available in {target}: {', '.join(available) or '(none)'}."
            )
    return violations
