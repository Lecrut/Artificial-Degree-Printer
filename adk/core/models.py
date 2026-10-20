from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

TaskStatus = Literal["TODO", "IN_PROGRESS", "DONE", "FAILED"]
GateVerdict = Literal["PASS", "FAIL"]
ModelTier = Literal["SML", "LRM"]


@dataclass(slots=True)
class TaskItem:
    """Single atomic task in state/task_queue.json."""

    task_id: str
    description: str
    target_node: str
    assigned_agent: str
    status: TaskStatus = "TODO"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskItem:
        return cls(
            task_id=str(data["task_id"]),
            description=str(data["description"]),
            target_node=str(data["target_node"]),
            assigned_agent=str(data["assigned_agent"]),
            status=data.get("status", "TODO"),
        )


@dataclass(slots=True)
class HypergraphMatrix:
    """Structured representation of state/hypergraph_matrix.json."""

    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    edges: dict[str, list[str]] = field(default_factory=dict)
    matrix: dict[str, dict[str, int]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": self.nodes,
            "edges": self.edges,
            "matrix": self.matrix,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HypergraphMatrix:
        return cls(
            nodes=dict(data.get("nodes", {})),
            edges={k: list(v) for k, v in data.get("edges", {}).items()},
            matrix={k: dict(v) for k, v in data.get("matrix", {}).items()},
        )


@dataclass(slots=True)
class ValidationReport:
    """Structured representation of state/validation_report.json."""

    status: GateVerdict
    failed_task_id: str | None = None
    failed_node: str | None = None
    failed_file: str | None = None
    failed_agent: str | None = None
    supervisors: dict[str, dict[str, Any]] = field(default_factory=dict)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EvolutionEvent:
    """Single entry in state/evolution_history.json."""

    type: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type, **self.details}


def resolve_adk_path(path_or_rel: str | Path) -> Path:
    """Resolve a path either directly on disk or relative to the adk/ package root."""
    candidate = Path(path_or_rel)
    if candidate.exists():
        return candidate
    adk_root = Path(__file__).resolve().parent.parent
    alt = adk_root / candidate
    if alt.exists():
        return alt
    # Also strip leading 'adk/' if caller passed 'adk/state/...'
    parts = candidate.parts
    if parts and parts[0].lower() == "adk":
        stripped = adk_root.joinpath(*parts[1:])
        if stripped.exists():
            return stripped
        return stripped
    return alt


def read_json_state(path_or_rel: str | Path) -> Any:
    """Read and parse a JSON state file."""
    resolved = resolve_adk_path(path_or_rel)
    return json.loads(resolved.read_text(encoding="utf-8"))


def write_json_state(path_or_rel: str | Path, payload: Any) -> Path:
    """Serialize and write a JSON state file with consistent formatting."""
    resolved = resolve_adk_path(path_or_rel)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return resolved

