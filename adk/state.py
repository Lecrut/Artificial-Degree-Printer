from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any
from adk.core.state import ADKProjectState


@dataclass
class RunState:
    request: str
    requirements: list[str]
    plan: list[str]
    changes: list[str]
    verification: list[str]
    notes: list[str]


def state_to_dict(state: RunState | ADKProjectState) -> dict[str, Any]:
    if isinstance(state, ADKProjectState):
        return state.model_dump()
    return asdict(state)
