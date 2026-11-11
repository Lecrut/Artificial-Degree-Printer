from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

from adk.core.models import read_json_state, resolve_adk_path, write_json_state


EXCLUDED_WORKSPACE_PARTS = {
    "benchmarks",
    "__pycache__",
    ".git",
    ".venv",
    ".pytest_cache",
    ".ruff_cache",
}


def _next_index(ids: dict[str, Any]) -> int:
    """Next free numeric suffix for ids like 'E12' / 'v7'; len()+1 collided after removals left gaps."""
    nums = [int(i[1:]) for i in ids if i[1:].isdigit()]
    return max(nums, default=0) + 1


def sync_hypergraph_matrix(
    workspace_dir: str | Path = "workspace",
    matrix_path: str | Path = "state/hypergraph_matrix.json",
) -> dict[str, Any]:
    """Scan .py imports and \\ref_ast / \\ref_csv tags in workspace/ and update hypergraph_matrix.json, excluding benchmarks/ and internal caches."""
    w_dir = resolve_adk_path(workspace_dir)
    data = read_json_state(matrix_path)
    nodes: dict[str, dict[str, Any]] = data.get("nodes", {})
    edges: dict[str, list[str]] = data.get("edges", {})
    matrix: dict[str, dict[str, int]] = data.get("matrix", {})
    edge_meta: dict[str, dict[str, Any]] = data.get("edge_meta", {})

    # Drop edges that were dynamically discovered in a previous sync; they are re-derived below from
    # current workspace code. Without this, the hypergraph grew monotonically (blast radius never shrank)
    # because removed imports / \ref tags left orphan edge memberships behind.
    for eid in [eid for eid, meta in edge_meta.items() if meta.get("dynamic")]:
        edges.pop(eid, None)
        edge_meta.pop(eid, None)

    # Prune any existing nodes that point to excluded directories (such as benchmarks/)
    valid_nodes: dict[str, dict[str, Any]] = {}
    excluded_node_ids: set[str] = set()
    for node_id, meta in nodes.items():
        rel_path = meta.get("path", "")
        if any(part in EXCLUDED_WORKSPACE_PARTS for part in Path(rel_path).parts):
            excluded_node_ids.add(node_id)
        else:
            valid_nodes[node_id] = meta
    nodes = valid_nodes

    if excluded_node_ids:
        clean_edges: dict[str, list[str]] = {}
        for edge_id, members in edges.items():
            clean_members = [m for m in members if m not in excluded_node_ids]
            if clean_members:
                clean_edges[edge_id] = clean_members
        edges = clean_edges

        clean_matrix: dict[str, dict[str, int]] = {}
        for n_id in nodes:
            row = matrix.get(n_id, {})
            clean_matrix[n_id] = {e_id: int(row.get(e_id, 0)) for e_id in edges}
        matrix = clean_matrix

    path_to_node: dict[str, str] = {}
    stem_to_node: dict[str, str] = {}
    for node_id, meta in nodes.items():
        rel_path = meta.get("path", "")
        if rel_path:
            path_to_node[rel_path] = node_id
            stem_to_node[Path(rel_path).stem] = node_id

    if w_dir.exists():
        for file_path in sorted(w_dir.rglob("*")):
            if (
                not file_path.is_file()
                or file_path.name == ".gitkeep"
                or any(part in EXCLUDED_WORKSPACE_PARTS for part in file_path.parts)
            ):
                continue
            rel = file_path.relative_to(w_dir).as_posix()
            if rel not in path_to_node:
                new_id = f"v{_next_index(nodes)}"
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
            for match in re.finditer(r"\\ref_fig\{([^}]+)\}", content):
                fig_file = match.group(1).strip()
                target_node = path_to_node.get(fig_file) or stem_to_node.get(Path(fig_file).stem)
                if target_node and target_node != src_node:
                    dynamic_couplings.append((src_node, target_node))
            for match in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", content):

                gfx_path = match.group(1).strip()
                target_node = path_to_node.get(gfx_path) or stem_to_node.get(Path(gfx_path).stem)
                if target_node and target_node != src_node:
                    dynamic_couplings.append((src_node, target_node))
            if re.search(r"\\cite\{([^}]+)\}", content):
                for bib_rel, bib_node in path_to_node.items():
                    if bib_rel.endswith(".bib") and bib_node != src_node:
                        dynamic_couplings.append((src_node, bib_node))

    for node_a, node_b in dynamic_couplings:
        pair_set = {node_a, node_b}
        matched_edge = None
        for edge_id, members in edges.items():
            if pair_set.issubset(set(members)):
                matched_edge = edge_id
                break
        if matched_edge is None:
            matched_edge = f"E{_next_index(edges)}"
            edges[matched_edge] = sorted(pair_set)
            edge_meta[matched_edge] = {"dynamic": True}

    # A hyperedge couples at least two files; single-member edges (left behind by node pruning) only
    # inflated d(v), forcing those nodes onto the LRM tier and widening the blast radius.
    edges = {e_id: members for e_id, members in edges.items() if len(set(members)) >= 2}
    edge_meta = {e_id: meta for e_id, meta in edge_meta.items() if e_id in edges}

    # Rebuild the incidence matrix entirely from current edge memberships so stale entries from
    # removed couplings do not linger (previously `row[e_id]` preserved old values for non-members).
    all_edge_ids = list(edges.keys())
    matrix = {n_id: {e_id: (1 if n_id in edges[e_id] else 0) for e_id in all_edge_ids} for n_id in nodes}
    for n_id, meta in nodes.items():
        meta["degree"] = sum(int(v) for v in matrix[n_id].values())

    write_json_state(
        matrix_path,
        {
            "nodes": nodes,
            "edges": edges,
            "matrix": matrix,
            "edge_meta": edge_meta,
        },
    )
    return {
        "status": "ok",
        "nodes_count": len(nodes),
        "edges_count": len(edges),
        "degrees": {n_id: meta["degree"] for n_id, meta in nodes.items()},
    }

