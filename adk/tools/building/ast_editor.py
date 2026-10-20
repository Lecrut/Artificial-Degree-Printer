from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


def edit_ast_node(
    file_path: str | Path,
    target_name: str,
    new_code: str,
) -> dict[str, Any]:
    """Replace or append a function/class/assignment AST node in a .py file with built-in syntax GUARD."""
    path = Path(file_path)

    # 1. Syntax GUARD on incoming snippet
    try:
        snippet_tree = ast.parse(new_code)
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

    new_node = snippet_tree.body[0]

    if path.exists():
        existing_source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(existing_source)
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

    replaced = False
    new_body: list[ast.stmt] = []
    for node in tree.body:
        node_name = None
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            node_name = node.name
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == target_name:
                    node_name = target.id
                    break

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

