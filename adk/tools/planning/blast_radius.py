from __future__ import annotations

from pathlib import Path
from typing import Any

from adk.core.models import read_json_state


def calculate_blast_radius(
    modified_node_id: str,
    matrix_path: str | Path = "state/hypergraph_matrix.json",
) -> dict[str, Any]:
    """Calculate the hypergraph blast radius and node degree d(v) for a modified node."""
    data = read_json_state(matrix_path)
    nodes: dict[str, Any] = data.get("nodes", {})
    matrix: dict[str, dict[str, int]] = data.get("matrix", {})

    if modified_node_id not in matrix:
        raise KeyError(f"Node '{modified_node_id}' not found in hypergraph incidence matrix.")

    node_row = matrix[modified_node_id]
    active_edges = [edge_id for edge_id, val in node_row.items() if int(val) == 1]
    degree = sum(int(val) for val in node_row.values())

    affected_nodes: list[str] = []
    affected_files: list[str] = []

    for other_node_id, other_row in matrix.items():
        if other_node_id == modified_node_id:
            continue
        if any(int(other_row.get(edge_id, 0)) == 1 for edge_id in active_edges):
            affected_nodes.append(other_node_id)
            file_path = nodes.get(other_node_id, {}).get("path")
            if file_path:
                affected_files.append(file_path)

    return {
        "modified_node_id": modified_node_id,
        "modified_file": nodes.get(modified_node_id, {}).get("path"),
        "degree": degree,
        "active_edges": active_edges,
        "affected_nodes": affected_nodes,
        "affected_files": affected_files,
    }


def get_scoped_hypergraph_context(
    matrix_path: str | Path = "state/hypergraph_matrix.json",
    blast_radius: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Extract lightweight hypergraph context: nodes and active hyperedges relevant to blast radius, omitting raw 0/1 incidence matrix."""
    data = read_json_state(matrix_path)
    nodes: dict[str, Any] = data.get("nodes", {})
    all_edges: dict[str, list[str]] = data.get("edges", {})

    active_edge_ids: set[str] = set()
    if blast_radius and "active_edges" in blast_radius:
        active_edge_ids.update(blast_radius["active_edges"])

    if not active_edge_ids and blast_radius:
        relevant_nodes = set(blast_radius.get("affected_nodes", []))
        if blast_radius.get("modified_node_id"):
            relevant_nodes.add(blast_radius["modified_node_id"])
        for e_id, members in all_edges.items():
            if any(m in relevant_nodes for m in members):
                active_edge_ids.add(e_id)

    scoped_edges: dict[str, list[str]] = {}
    for e_id in sorted(active_edge_ids):
        if e_id in all_edges:
            scoped_edges[e_id] = all_edges[e_id]

    if not scoped_edges and all_edges:
        for e_id in sorted(all_edges.keys())[:5]:
            scoped_edges[e_id] = all_edges[e_id]

    scoped_nodes: dict[str, dict[str, Any]] = {}
    for n_id, meta in nodes.items():
        scoped_nodes[n_id] = {
            "path": meta.get("path"),
            "degree": meta.get("degree", 0),
            "weight": meta.get("weight", 1.0),
        }

    return {
        "nodes": scoped_nodes,
        "active_edges": scoped_edges,
    }

