from __future__ import annotations

from pathlib import Path
from typing import Any

from adk.core.models import ModelTier, read_json_state, write_json_state


def select_model_tier(
    node_id: str,
    matrix_path: str | Path = "state/hypergraph_matrix.json",
) -> ModelTier:
    """Select 'LRM' if d(v) >= 2 or w(v) > 1.5, otherwise 'SML'."""
    data = read_json_state(matrix_path)
    nodes: dict[str, Any] = data.get("nodes", {})
    matrix: dict[str, dict[str, int]] = data.get("matrix", {})

    if node_id not in nodes and node_id not in matrix:
        for n_key, n_meta in nodes.items():
            if n_meta.get("path") == node_id or Path(str(n_meta.get("path", ""))).name == Path(node_id).name:
                node_id = n_key
                break

    if node_id not in nodes and node_id not in matrix:
        # Graceful fallback: return LRM for unknown nodes to be safe and never crash
        return "LRM"

    node_meta = nodes.get(node_id, {})
    row = matrix.get(node_id, {})

    degree = sum(int(v) for v in row.values()) if row else int(node_meta.get("degree", 0))
    weight = float(node_meta.get("weight", 1.0))

    if degree >= 2 or weight > 1.5:
        return "LRM"
    return "SML"


def escalate_node_weight(
    node_id: str,
    delta: float = 0.4,
    matrix_path: str | Path = "state/hypergraph_matrix.json",
) -> dict[str, Any]:
    """Increase weight w(v) of node_id in hypergraph_matrix.json by delta (EvoRoute) and return updated routing tier."""
    data = read_json_state(matrix_path)
    nodes: dict[str, Any] = data.get("nodes", {})
    matrix: dict[str, dict[str, int]] = data.get("matrix", {})

    if node_id not in nodes and node_id not in matrix:
        for n_key, n_meta in nodes.items():
            if n_meta.get("path") == node_id or Path(str(n_meta.get("path", ""))).name == Path(node_id).name:
                node_id = n_key
                break

    if node_id not in nodes:
        # Never invent a node: an unknown id used to create '<id>.py', a path pointing at no file.
        return {"node_id": node_id, "status": "unknown_node", "tier": select_model_tier(node_id, matrix_path)}

    old_tier = select_model_tier(node_id, matrix_path)
    node_meta = nodes[node_id]
    row = matrix.get(node_id, {})
    degree = sum(int(v) for v in row.values()) if row else int(node_meta.get("degree", 0))

    old_weight = float(node_meta.get("weight", 1.0))
    new_weight = round(old_weight + float(delta), 2)
    node_meta["weight"] = new_weight
    node_meta["degree"] = degree

    write_json_state(matrix_path, data)
    new_tier = select_model_tier(node_id, matrix_path)

    return {
        "node_id": node_id,
        "old_weight": old_weight,
        "new_weight": new_weight,
        "delta": round(float(delta), 2),
        "degree": degree,
        "old_tier": old_tier,
        "new_tier": new_tier,
        "tier": new_tier,
    }


