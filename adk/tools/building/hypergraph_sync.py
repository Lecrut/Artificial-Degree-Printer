from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

from adk.core.models import read_json_state, resolve_adk_path, write_json_state


def sync_hypergraph_matrix(
    workspace_dir: str | Path = "workspace",
    matrix_path: str | Path = "state/hypergraph_matrix.json",
) -> dict[str, Any]:
    """Scan .py imports and \\ref_ast / \\ref_csv tags in workspace/ and update hypergraph_matrix.json."""
    w_dir = resolve_adk_path(workspace_dir)
    data = read_json_state(matrix_path)
    nodes: dict[str, dict[str, Any]] = data.get("nodes", {})
    edges: dict[str, list[str]] = data.get("edges", {})
    matrix: dict[str, dict[str, int]] = data.get("matrix", {})

    path_to_node: dict[str, str] = {}
    stem_to_node: dict[str, str] = {}
    for node_id, meta in nodes.items():
        rel_path = meta.get("path", "")
        if rel_path:
            path_to_node[rel_path] = node_id
            stem_to_node[Path(rel_path).stem] = node_id

    if w_dir.exists():
        for file_path in sorted(w_dir.rglob("*")):
            if not file_path.is_file() or file_path.name == ".gitkeep" or "__pycache__" in file_path.parts:
                continue
            rel = file_path.relative_to(w_dir).as_posix()
            if rel not in path_to_node:
                new_id = f"v{len(nodes) + 1}"
                nodes[new_id] = {"path": rel, "degree": 0, "weight": 1.0}
                matrix[new_id] = {e_id: 0 for e_id in edges}
                path_to_node[rel] = new_id
                stem_to_node[file_path.stem] = new_id

    dynamic_couplings: list[tuple[str, str]] = []
    for rel_path, src_node in list(path_to_node.items()):
        full_path = w_dir / rel_path
        if not full_path.exists():
            continue

        content = full_path.read_text(encoding="utf-8", errors="ignore")
        if rel_path.endswith(".py"):
            try:
                tree = ast.parse(content)
                for stmt in ast.walk(tree):
                    if isinstance(stmt, ast.Import):
                        for alias in stmt.names:
                            mod_stem = alias.name.split(".")[-1]
                            if mod_stem in stem_to_node and stem_to_node[mod_stem] != src_node:
                                dynamic_couplings.append((src_node, stem_to_node[mod_stem]))
                    elif isinstance(stmt, ast.ImportFrom) and stmt.module:
                        mod_stem = stmt.module.split(".")[-1]
                        if mod_stem in stem_to_node and stem_to_node[mod_stem] != src_node:
                            dynamic_couplings.append((src_node, stem_to_node[mod_stem]))
            except SyntaxError:
                pass
        elif rel_path.endswith((".md", ".tex")):
            for match in re.finditer(r"\\ref_(?:ast|csv)\{([^:}]+):([^}]+)\}", content):
                ref_file = match.group(1).strip()
                target_node = path_to_node.get(ref_file) or stem_to_node.get(Path(ref_file).stem)
                if target_node and target_node != src_node:
                    dynamic_couplings.append((src_node, target_node))

    for node_a, node_b in dynamic_couplings:
        pair_set = {node_a, node_b}
        matched_edge = None
        for edge_id, members in edges.items():
            if pair_set.issubset(set(members)):
                matched_edge = edge_id
                break
        if matched_edge is None:
            matched_edge = f"E{len(edges) + 1}"
            edges[matched_edge] = sorted(pair_set)
            for n_id in nodes:
                matrix.setdefault(n_id, {})[matched_edge] = 1 if n_id in pair_set else 0

    all_edge_ids = list(edges.keys())
    for n_id in nodes:
        row = matrix.setdefault(n_id, {})
        for e_id in all_edge_ids:
            row[e_id] = 1 if n_id in edges[e_id] else int(row.get(e_id, 0))
            if row[e_id] == 1 and n_id not in edges[e_id]:
                edges[e_id].append(n_id)
        degree = sum(int(v) for v in row.values())
        nodes[n_id]["degree"] = degree

    write_json_state(
        matrix_path,
        {
            "nodes": nodes,
            "edges": edges,
            "matrix": matrix,
        },
    )
    return {
        "status": "ok",
        "nodes_count": len(nodes),
        "edges_count": len(edges),
        "degrees": {n_id: meta["degree"] for n_id, meta in nodes.items()},
    }

