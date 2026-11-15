from __future__ import annotations

import ast
import csv
from pathlib import Path
from typing import Any

from adk.core.models import read_json_state, resolve_adk_path


def class_method_signatures(cls: ast.ClassDef) -> dict[str, str]:
    """`Class.member` -> its signature: `__init__` and public methods, plus public class attributes (among them
    Enum members — without these a tester guessed names like `Player.PLAYER_ONE`, 2026-11-14 run)."""
    out: dict[str, str] = {}
    for item in cls.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
            item.name == "__init__" or not item.name.startswith("_")
        ):
            ret = f" -> {ast.unparse(item.returns)}" if item.returns is not None else ""
            out[f"{cls.name}.{item.name}"] = f"def {item.name}({ast.unparse(item.args)}){ret}"
        elif isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    out[f"{cls.name}.{target.id}"] = f"{target.id} = {ast.unparse(item.value)}"[:120]
        elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name) and not item.target.id.startswith("_"):
            value = f" = {ast.unparse(item.value)}" if item.value is not None else ""
            out[f"{cls.name}.{item.target.id}"] = f"{item.target.id}: {ast.unparse(item.annotation)}{value}"[:120]
    return out


def module_import_path(rel_path: str) -> str:
    """Dotted import path of a workspace module (`src/data/gen.py` -> `src.data.gen`, `src/__init__.py` -> `src`)."""
    parts = Path(rel_path).with_suffix("").parts
    return ".".join(p for p in parts if p != "__init__")


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
                exports_by_file[rel_path] = {"functions": [], "classes": [], "variables": [], "import": module_import_path(rel_path)}
                continue

            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8"))
            except SyntaxError:
                exports_by_file[rel_path] = {"functions": [], "classes": [], "variables": [], "import": module_import_path(rel_path)}
                continue

            functions: list[str] = []
            signatures: dict[str, str] = {}
            docstrings: dict[str, str] = {}
            classes: list[str] = []
            variables: list[str] = []

            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
                    functions.append(node.name)
                    try:
                        args_unparsed = ast.unparse(node.args) if hasattr(ast, "unparse") else ""
                        ret_unparsed = f" -> {ast.unparse(node.returns)}" if getattr(node, "returns", None) else ""
                        signatures[node.name] = f"def {node.name}({args_unparsed}){ret_unparsed}"
                    except Exception:
                        signatures[node.name] = f"def {node.name}(...)"
                    doc = ast.get_docstring(node)
                    if doc:
                        docstrings[node.name] = doc[:300]
                elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                    classes.append(node.name)
                    doc = ast.get_docstring(node)
                    if doc:
                        docstrings[node.name] = doc[:300]
                    # The class API: without method signatures a tester could only guess them (2026-11-12 run).
                    signatures.update(class_method_signatures(node))
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and not target.id.startswith("_"):
                            variables.append(target.id)
                elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                    if not node.target.id.startswith("_"):
                        variables.append(node.target.id)

            exports_by_file[rel_path] = {
                "functions": functions,
                "signatures": signatures,
                "docstrings": docstrings,
                "classes": classes,
                "variables": variables,
                # The one true way to import this module (`from src.data.gen import X`); without it a tester
                # guessed `import synthetic_data_generator` for a module living in a package (2026-11-14, D2).
                "import": module_import_path(rel_path),
            }
        elif rel_path.endswith(".csv"):
            csv_file = w_dir / rel_path
            if csv_file.exists():
                with csv_file.open("r", encoding="utf-8", newline="") as f:
                    reader = list(csv.DictReader(f))
                    cols = list(reader[0].keys()) if reader else []
                    first_col = cols[0] if cols else None
                    if {"method", "metric"} <= set(cols):
                        # Tidy schema: a row is identified by the pair, cited as `file:method+metric:value`.
                        row_keys = [f"{r['method']}+{r['metric']}" for r in reader if r.get("method") and r.get("metric")]
                    else:
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

