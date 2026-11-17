from __future__ import annotations

import ast
import textwrap
import warnings
from pathlib import Path
from typing import Any


def _is_main_guard(node: ast.stmt) -> bool:
    return isinstance(node, ast.If) and ast.unparse(node.test).replace("'", '"') == '__name__ == "__main__"'


def _extract_stmt_name(node: ast.stmt) -> str | None:
    """Return the symbol name defined by an AST statement (function, class, Assign, AnnAssign, `__main__` block)."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return node.name
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                return target.id
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id
    if _is_main_guard(node):
        return "__main__"
    return None


def _is_docstring(node: ast.stmt) -> bool:
    return isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)


def _parse(source: str, path: Path) -> ast.Module:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=SyntaxWarning)
        return ast.parse(source, filename=str(path))


def _error(guard: str, path: Path, target_name: str, error: str) -> dict[str, Any]:
    return {"status": "error", "guard": guard, "file": str(path), "target_name": target_name, "error": error}


def declared_names(source: str) -> set[str]:
    """Names a module declares: constants, functions, classes and `Class.method` — what a planned interface
    (the plan's stub source) allows the module to contain."""
    names: set[str] = set()
    for node in ast.parse(source).body:
        name = _extract_stmt_name(node)
        if name:
            names.add(name)
        if isinstance(node, ast.ClassDef):
            names |= {f"{node.name}.{n}" for s in node.body if (n := _extract_stmt_name(s))}
    return names


def _may_append(path: Path, name: str, planned: set[str] | None) -> bool:
    """A symbol the file does not have is added when the plan declares it for this module, or where adding is
    ordinary work: a private helper, a test file, the `__main__` block. Without a planned interface for the file
    there is nothing to judge against. On 2026-11-16 edits of `fit`/`predict` aimed at the wrong file were
    appended to `experiment.py` (planned: only `run_experiment`) and became part of the contract (Audit VI X3)."""
    is_test = path.name.startswith("test_") or "tests" in path.parts
    last = name.rpartition(".")[2]
    return planned is None or name in planned or last.startswith("_") or last == "__main__" or is_test


def _used_names(body: list[ast.stmt]) -> set[str]:
    return {
        n.id
        for stmt in body
        if not isinstance(stmt, (ast.Import, ast.ImportFrom))
        for n in ast.walk(stmt)
        if isinstance(n, ast.Name)
    }


def _merge_imports(body: list[ast.stmt], new_imports: list[ast.stmt], insert_at: int) -> list[ast.stmt]:
    """Imports of the edit join the module's imports. A `from M import …` of a module the file already imports
    from becomes ONE statement: every name of the edit plus the old names still used in the module. Before,
    imports were only ever added, so a stale `from src.config import N_REPETITIONS` could not be removed by
    any symbol edit and stayed as the run's final ImportError (Audit VI X3c)."""
    body = list(body)
    for imp in new_imports:
        if isinstance(imp, ast.Import) or any(a.name == "*" for a in imp.names):
            if ast.dump(imp) not in {ast.dump(n) for n in body}:
                body.insert(insert_at, imp)
                insert_at += 1
            continue
        same = [n for n in body if isinstance(n, ast.ImportFrom) and n.module == imp.module and n.level == imp.level]
        if not same:
            body.insert(insert_at, imp)
            insert_at += 1
            continue
        used = _used_names(body)
        names = {a.asname or a.name: a for a in imp.names}
        for old in same:
            for alias in old.names:
                key = alias.asname or alias.name
                if key not in names and key in used:
                    names[key] = alias
        merged = ast.ImportFrom(module=imp.module, names=list(names.values()), level=imp.level)
        first = body.index(same[0])
        body[first] = merged
        body = [n for n in body if not any(n is old for old in same[1:])]
    return body


def whole_module_loss(old_source: str, new_source: str) -> list[str]:
    """Public top-level names of the existing module that a whole-module answer would drop. An `ast_edits`
    element named after the module replaces the whole file; on 2026-11-16 three import lines sent that way
    overwrote all of `experiment.py` (Audit VI X3e)."""
    try:
        old_names = {name for n in ast.parse(old_source).body if (name := _extract_stmt_name(n))}
        new_names = {name for n in ast.parse(new_source).body if (name := _extract_stmt_name(n))}
    except SyntaxError:
        return []  # a parse error is reported by the syntax guard of the write itself
    return sorted(n for n in old_names - new_names if not n.startswith("_") and n != "__main__")


def edit_ast_node(
    file_path: str | Path,
    target_name: str,
    new_code: str,
    planned: set[str] | None = None,
) -> dict[str, Any]:
    """Replace one function/class/assignment/method of a .py file (or add it where adding is allowed, see
    `_may_append`; `planned` = names of the module's planned interface), with a syntax GUARD. Anything the edit
    cannot apply exactly is an error for the agent, never a silent change."""
    path = Path(file_path)
    # A method is naturally returned with its class indentation; indented code is not a syntax error.
    new_code = textwrap.dedent(new_code)
    try:
        snippet_tree = _parse(new_code, path)
    except SyntaxError as exc:
        return _error("SYNTAX_GUARD_REJECTED", path, target_name, f"SyntaxError in new_code: {exc}")
    if not snippet_tree.body:
        return _error("SYNTAX_GUARD_REJECTED", path, target_name, "Provided new_code contains no AST statements.")

    # `Class.method` edits one method inside a class instead of a top-level symbol.
    class_name, _, method_name = target_name.rpartition(".")
    lookup_name = method_name if class_name else target_name

    matching_stmt: ast.stmt | None = None
    extra_imports: list[ast.stmt] = []
    extra_defs: list[str] = []
    for stmt in snippet_tree.body:
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            extra_imports.append(stmt)
        elif matching_stmt is None and _extract_stmt_name(stmt) == lookup_name:
            matching_stmt = stmt
        elif matching_stmt is None and class_name and isinstance(stmt, ast.ClassDef) and stmt.name == class_name:
            # the snippet repeats the class around the method: take the method out of it
            members = [s for s in stmt.body if not _is_docstring(s)]
            matching_stmt = next((s for s in members if _extract_stmt_name(s) == lookup_name), None)
            extra_defs += [str(_extract_stmt_name(s)) for s in members if s is not matching_stmt]
        elif not _is_docstring(stmt):
            extra_defs.append(str(_extract_stmt_name(stmt) or type(stmt).__name__))

    if matching_stmt is None:
        return _error(
            "TARGET_NOT_IN_CODE", path, target_name,
            f"The new code of {target_name} contains no definition of `{lookup_name}`; nothing was saved.",
        )
    if extra_defs:
        return _error(
            "EXTRA_DEFINITIONS", path, target_name,
            f"The new code of {target_name} also contains {', '.join(extra_defs)}; nothing was saved. Send every "
            "symbol as its own element of ast_edits, or the whole file in `files`.",
        )

    if path.exists():
        try:
            tree = _parse(path.read_text(encoding="utf-8"), path)
        except SyntaxError as exc:
            return _error("SYNTAX_GUARD_REJECTED", path, target_name, f"Existing file has SyntaxError: {exc}")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        tree = ast.Module(body=[], type_ignores=[])

    # Leading module docstring and `from __future__` imports stay first.
    idx = 1 if tree.body and _is_docstring(tree.body[0]) else 0
    while idx < len(tree.body) and isinstance(tree.body[idx], ast.ImportFrom) and tree.body[idx].module == "__future__":
        idx += 1

    if class_name:
        owner = next((n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name), None)
        if owner is None:
            return _error(
                "TARGET_NOT_FOUND", path, target_name,
                f"Class {class_name} does not exist in {path.name}; the edit of {target_name} has nowhere to land.",
            )
        scope = owner.body
    else:
        scope = tree.body

    hits = [i for i, n in enumerate(scope) if _extract_stmt_name(n) == lookup_name]
    if len(hits) > 1:
        # Python uses the LAST definition, the edit used to replace the first: repairs landed in dead code
        # (2026-11-16: three `run_experiment` in experiment.py).
        return _error(
            "DUPLICATE_DEFINITION", path, target_name,
            f"`{target_name}` is defined {len(hits)} times in {path.name} (Python uses only the last one); nothing "
            "was saved. Return the whole file in `files` with exactly one definition.",
        )
    if hits:
        scope[hits[0]] = matching_stmt
        action = "replaced"
    elif not path.exists() or _may_append(path, target_name, planned):
        scope.append(matching_stmt)
        action = "appended"
    else:
        existing = sorted(declared_names(ast.unparse(tree)))
        return _error(
            "TARGET_NOT_FOUND", path, target_name,
            f"{path.name} has no `{target_name}` and the planned interface of this module does not declare it "
            f"(the file has: {', '.join(existing) or 'nothing'}); nothing was saved. Edit one of these symbols, or "
            "check that this edit belongs to this file.",
        )

    tree.body = _merge_imports(tree.body, extra_imports, idx)
    ast.fix_missing_locations(tree)
    rendered_code = ast.unparse(tree) + "\n"

    # Final full-file Syntax GUARD before writing to disk
    try:
        ast.parse(rendered_code)
    except SyntaxError as exc:
        return _error("SYNTAX_GUARD_REJECTED", path, target_name, f"Rendered file failed SyntaxError guard: {exc}")

    path.write_text(rendered_code, encoding="utf-8")
    return {
        "status": "ok",
        "guard": "SYNTAX_GUARD_PASSED",
        "file": str(path),
        "target_name": target_name,
        "action": action,
    }
