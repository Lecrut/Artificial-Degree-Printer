from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

TaskStatus = Literal["TODO", "WAITING", "IN_PROGRESS", "DONE", "FAILED"]
GateVerdict = Literal["PASS", "FAIL"]
ModelTier = Literal["SML", "LRM"]


def forced_tier() -> ModelTier | None:
    """The one tier every call uses, or None for the two-tier design (the small model works, the large one escalates).
    `HARNESS_FORCE_TIER` = `SML` | `LRM` | `none`; unset means `LRM`: until the harness is closed the large model does
    everything (decision of 2026-11-26), and small models are tried afterwards. The two tiers stay in the code and in
    `.env`; this only decides which one a call gets."""
    value = os.environ.get("HARNESS_FORCE_TIER", "LRM").strip().upper()
    return value if value in ("SML", "LRM") else None  # type: ignore[return-value]


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


# The files of one run in a `state/` folder, in their empty form. A run starts from these (a benchmark sandbox, a
# scenario of main.py); the repository's adk/state keeps them empty and holds only the agent registry as data.
RUNTIME_STATE_EMPTY: dict[str, Any] = {
    "task_queue.json": [],
    "validation_report.json": {
        "status": "PASS",
        "failed_task_id": None,
        "failed_node": None,
        "failed_file": None,
        "failed_agent": None,
        "supervisors": {},
        "summary": "",
    },
    "failure_ledger.json": {"failures": []},
    "evolution_history.json": {"events": []},
    "hitl_flag.json": {"active": False, "current_gate": None, "approved_gates": [], "question": None, "context": {}},
}


def reset_runtime_state(state_dir: str | Path) -> None:
    """Write every run file of `state_dir` in its empty form."""
    for name, empty in RUNTIME_STATE_EMPTY.items():
        write_json_state(Path(state_dir) / name, empty)

