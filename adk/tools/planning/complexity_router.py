from __future__ import annotations

from pathlib import Path
from typing import Any

from adk.core.models import ModelTier, read_json_state, write_json_state

# The small model does the work. The large one steps in for one attempt after the small model failed a task
# this many times; a failure never promotes the node for the rest of the run (Audit IV §IV.8).
ESCALATE_TO_LRM_AFTER = 2


def select_model_tier(failures: int = 0) -> ModelTier:
    """Tier for a build attempt: 'SML' by default, 'LRM' once the small model has failed `failures` times.

    Until 2026-11-14 the tier followed the node (`degree >= 2 or weight > 1.5`), which in any project with code,
    tests and a thesis meant LRM for almost every task and, after the weight escalation, for the rest of the run:
    83% of the 2026-11-13 run's model time went to the large model."""
    return "LRM" if int(failures) >= ESCALATE_TO_LRM_AFTER else "SML"


def escalate_node_weight(
    node_id: str,
    delta: float = 0.4,
    matrix_path: str | Path = "state/hypergraph_matrix.json",
) -> dict[str, Any]:
    """Increase weight w(v) of node_id in hypergraph_matrix.json by delta (EvoRoute bookkeeping of how much
    trouble a node gave). The weight no longer selects the model tier."""
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
        return {"node_id": node_id, "status": "unknown_node"}

    node_meta = nodes[node_id]
    row = matrix.get(node_id, {})
    degree = sum(int(v) for v in row.values()) if row else int(node_meta.get("degree", 0))

    old_weight = float(node_meta.get("weight", 1.0))
    new_weight = round(old_weight + float(delta), 2)
    node_meta["weight"] = new_weight
    node_meta["degree"] = degree

    write_json_state(matrix_path, data)

    return {
        "node_id": node_id,
        "old_weight": old_weight,
        "new_weight": new_weight,
        "delta": round(float(delta), 2),
        "degree": degree,
    }
