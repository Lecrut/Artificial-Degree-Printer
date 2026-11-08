from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


def _extract_stmt_name(node: ast.stmt) -> str | None:
    """Return the symbol name defined by an AST statement (function, class, Assign, or AnnAssign)."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return node.name
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                return target.id
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id
    return None


def edit_ast_node(
    file_path: str | Path,
    target_name: str,
    new_code: str,
) -> dict[str, Any]:
    """Replace or append a function/class/assignment AST node in a .py file with built-in syntax GUARD."""
    path = Path(file_path)

    # 1. Syntax GUARD on incoming snippet
    import warnings
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=SyntaxWarning)
            snippet_tree = ast.parse(new_code, filename=str(path))
    except SyntaxError as exc:
        return {
            "status": "error",
            "guard": "SYNTAX_GUARD_REJECTED",
            "file": str(path),
            "target_name": target_name,
            "error": f"SyntaxError in new_code: {exc}",
        }

    if not snippet_tree.body:
        return {
            "status": "error",
            "guard": "SYNTAX_GUARD_REJECTED",
            "file": str(path),
            "target_name": target_name,
            "error": "Provided new_code contains no AST statements.",
        }

    # Find the primary statement matching target_name if multiple statements (e.g. imports + def) were provided
    matching_stmt = None
    extra_imports: list[ast.stmt] = []
    for stmt in snippet_tree.body:
        if _extract_stmt_name(stmt) == target_name and matching_stmt is None:
            matching_stmt = stmt
        elif isinstance(stmt, (ast.Import, ast.ImportFrom)):
            extra_imports.append(stmt)

    new_node = matching_stmt if matching_stmt is not None else snippet_tree.body[-1]

    if path.exists():
        existing_source = path.read_text(encoding="utf-8")
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=SyntaxWarning)
                tree = ast.parse(existing_source, filename=str(path))
        except SyntaxError as exc:
            return {
                "status": "error",
                "guard": "SYNTAX_GUARD_REJECTED",
                "file": str(path),
                "target_name": target_name,
                "error": f"Existing file has SyntaxError: {exc}",
            }
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        tree = ast.Module(body=[], type_ignores=[])

    existing_import_dumps = {
        ast.dump(node) for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))
    }
    deduped_imports = [imp for imp in extra_imports if ast.dump(imp) not in existing_import_dumps]

    # Preserve leading module docstring and any `from __future__` imports before new imports
    prefix_nodes: list[ast.stmt] = []
    rest_nodes: list[ast.stmt] = []
    idx = 0
    if tree.body and isinstance(tree.body[0], ast.Expr):
        val = getattr(tree.body[0], "value", None)
        if isinstance(val, ast.Constant) and isinstance(val.value, str):
            prefix_nodes.append(tree.body[0])
            idx = 1

    while idx < len(tree.body):
        stmt = tree.body[idx]
        if isinstance(stmt, ast.ImportFrom) and stmt.module == "__future__":
            prefix_nodes.append(stmt)
            idx += 1
        else:
            break

    rest_nodes = list(tree.body[idx:])

    replaced = False
    new_body: list[ast.stmt] = list(prefix_nodes) + list(deduped_imports)
    for node in rest_nodes:
        node_name = _extract_stmt_name(node)
        if node_name == target_name and not replaced:
            new_body.append(new_node)
            replaced = True
        else:
            new_body.append(node)

    if not replaced:
        new_body.append(new_node)

    tree.body = new_body
    ast.fix_missing_locations(tree)
    rendered_code = ast.unparse(tree) + "\n"

    # 2. Final full-file Syntax GUARD before writing to disk
    try:
        ast.parse(rendered_code)
    except SyntaxError as exc:
        return {
            "status": "error",
            "guard": "SYNTAX_GUARD_REJECTED",
            "file": str(path),
            "target_name": target_name,
            "error": f"Rendered file failed SyntaxError guard: {exc}",
        }

    path.write_text(rendered_code, encoding="utf-8")
    return {
        "status": "ok",
        "guard": "SYNTAX_GUARD_PASSED",
        "file": str(path),
        "target_name": target_name,
        "action": "replaced" if replaced else "appended",
    }

