from __future__ import annotations

import ast
import csv
from pathlib import Path
from typing import Any

from adk.core.models import read_json_state, resolve_adk_path


def extract_hyperedge_exports(
    edge_id: str = "E1",
    matrix_path: str | Path = "state/hypergraph_matrix.json",
    workspace_dir: str | Path = "workspace",
    node_id: str | None = None,
) -> dict[str, Any]:
    """Extract exported AST symbols for .py files and CSV column/row schemas across hyperedges."""
    w_dir = resolve_adk_path(workspace_dir)
    data = read_json_state(matrix_path)
    nodes: dict[str, Any] = data.get("nodes", {})
    edges: dict[str, list[str]] = data.get("edges", {})
    matrix: dict[str, dict[str, int]] = data.get("matrix", {})

    if node_id and node_id in matrix:
        active_edges = [e_id for e_id, val in matrix[node_id].items() if int(val) == 1]
        if "E1" in edges and "E1" not in active_edges:
            active_edges.append("E1")
        target_node_ids: list[str] = []
        for e_id in active_edges:
            for n_id in edges.get(e_id, []):
                if n_id not in target_node_ids:
                    target_node_ids.append(n_id)
    elif edge_id == "ALL":
        target_node_ids = list(nodes.keys())
    else:
        target_node_ids = list(edges.get(edge_id, []))

    exports_by_file: dict[str, dict[str, list[str]]] = {}
    csv_schemas: dict[str, dict[str, list[str]]] = {}

    for n_id in target_node_ids:
        rel_path = nodes.get(n_id, {}).get("path", "")
        if rel_path.endswith(".py"):
            py_file = w_dir / rel_path
            if not py_file.exists():
                exports_by_file[rel_path] = {"functions": [], "classes": [], "variables": []}
                continue

            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8"))
            except SyntaxError:
                exports_by_file[rel_path] = {"functions": [], "classes": [], "variables": []}
                continue

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
                elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                    if not node.target.id.startswith("_"):
                        variables.append(node.target.id)

            exports_by_file[rel_path] = {
                "functions": functions,
                "classes": classes,
                "variables": variables,
            }
        elif rel_path.endswith(".csv"):
            csv_file = w_dir / rel_path
            if csv_file.exists():
                with csv_file.open("r", encoding="utf-8", newline="") as f:
                    reader = list(csv.DictReader(f))
                    cols = list(reader[0].keys()) if reader else []
                    first_col = cols[0] if cols else None
                    row_keys = (
                        [str(r[first_col]) for r in reader if first_col and r.get(first_col)]
                        if first_col
                        else []
                    )
                    csv_schemas[rel_path] = {
                        "columns": cols,
                        "row_selectors": row_keys,
                    }

    return {
        "status": "ok",
        "edge_id": edge_id,
        "exports": exports_by_file,
        "csv_schemas": csv_schemas,
    }

