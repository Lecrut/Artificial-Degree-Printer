from __future__ import annotations

from pathlib import Path
from typing import Any

from adk.core.models import ModelTier, read_json_state


def select_model_tier(
    node_id: str,
    matrix_path: str | Path = "state/hypergraph_matrix.json",
) -> ModelTier:
    """Select 'LRM' if d(v) >= 2 or w(v) > 1.5, otherwise 'SML'."""
    data = read_json_state(matrix_path)
    nodes: dict[str, Any] = data.get("nodes", {})
    matrix: dict[str, dict[str, int]] = data.get("matrix", {})

    if node_id not in nodes and node_id not in matrix:
        raise KeyError(f"Node '{node_id}' not found in hypergraph_matrix.json.")

    node_meta = nodes.get(node_id, {})
    row = matrix.get(node_id, {})

    degree = sum(int(v) for v in row.values()) if row else int(node_meta.get("degree", 0))
    weight = float(node_meta.get("weight", 1.0))

    if degree >= 2 or weight > 1.5:
        return "LRM"
    return "SML"

