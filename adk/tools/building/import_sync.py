from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from adk.core.models import read_json_state, resolve_adk_path


def extract_hyperedge_exports(
    edge_id: str = "E1",
    matrix_path: str | Path = "state/hypergraph_matrix.json",
    workspace_dir: str | Path = "workspace",
) -> dict[str, Any]:
    """Extract exported variable, function, and class names via AST for all .py files in a hyperedge."""
    w_dir = resolve_adk_path(workspace_dir)
    data = read_json_state(matrix_path)
    nodes: dict[str, Any] = data.get("nodes", {})
    edges: dict[str, list[str]] = data.get("edges", {})

    node_ids = edges.get(edge_id, [])
    exports_by_file: dict[str, dict[str, list[str]]] = {}

    for node_id in node_ids:
        rel_path = nodes.get(node_id, {}).get("path", "")
        if not rel_path.endswith(".py"):
            continue
        py_file = w_dir / rel_path
        if not py_file.exists():
            exports_by_file[rel_path] = {"functions": [], "classes": [], "variables": []}
            continue

        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        functions: list[str] = []
        classes: list[str] = []
        variables: list[str] = []

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                classes.append(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and not target.id.startswith("_"):
                        variables.append(target.id)

        exports_by_file[rel_path] = {
            "functions": functions,
            "classes": classes,
            "variables": variables,
        }

    return {
        "status": "ok",
        "edge_id": edge_id,
        "exports": exports_by_file,
    }

