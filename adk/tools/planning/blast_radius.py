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

