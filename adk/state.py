from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class RunState:
    request: str
    requirements: list[str]
    plan: list[str]
    changes: list[str]
    verification: list[str]
    notes: list[str]


def state_to_dict(state: RunState) -> dict[str, Any]:
    return asdict(state)
