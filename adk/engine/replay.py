from __future__ import annotations

import copy
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from adk.core.state import ADKProjectState


class ADKDeltaEvent(BaseModel):
    """Immutable snapshot of a single agent execution step."""

    step_index: int = Field(..., description="Sequential event index")
    stage_name: str = Field(..., description="Pipeline stage name (intake, research, architecture, etc.)")
    agent_name: str = Field(..., description="Name of the executing agent")
    timestamp: float = Field(default_factory=time.time, description="Unix timestamp")
    description: str = Field(..., description="Human-readable description of what happened")
    state_snapshot: Dict[str, Any] = Field(..., description="Full project state dump at this point")


class TimeTravelReplayEngine:
    """
    DARWIN-REPLAY 2027: Deterministic Multi-Agent Time-Travel Replay & Branching Engine.

    Core capabilities:
    - record_step(): Appends an immutable ADKDeltaEvent snapshot after each agent action.
    - rewind_to_step(K): Restores the full ADKProjectState to any historical step K.
    - branch_timeline(K, name): Forks execution into a parallel timeline from step K.
    - export_mermaid_timeline(): Generates a Mermaid diagram of the full trajectory.

    Scientific basis: @VMAO2026, @LivingHarness2026, @Zhou2026ExternalizationAgents.
    """

    def __init__(self, memory_dir: Optional[Path | str] = None) -> None:
        self.memory_dir = Path(memory_dir).resolve() if memory_dir else Path.cwd() / "adk" / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.events: List[ADKDeltaEvent] = []
        self.branches: Dict[str, List[ADKDeltaEvent]] = {}

    def record_step(
        self,
        stage_name: str,
        agent_name: str,
        state: ADKProjectState,
        description: str,
    ) -> ADKDeltaEvent:
        """Record an immutable delta event with a full state snapshot."""
        step_idx = len(self.events) + 1
        snapshot = state.model_dump(mode="json")
        event = ADKDeltaEvent(
            step_index=step_idx,
            stage_name=stage_name,
            agent_name=agent_name,
            description=description,
            state_snapshot=snapshot,
        )
        self.events.append(event)
        self._persist()
        return event

    def rewind_to_step(self, step_index: int) -> ADKProjectState:
        """Restore the project state to an exact historical step K."""
        if not self.events:
            raise ValueError("No events recorded in the replay trajectory.")
        if step_index < 1 or step_index > len(self.events):
            raise IndexError(
                f"Step index {step_index} out of trajectory range [1..{len(self.events)}]."
            )
        target_event = self.events[step_index - 1]
        return ADKProjectState.model_validate(target_event.state_snapshot)

    def branch_timeline(self, step_index: int, branch_name: str) -> ADKProjectState:
        """Fork execution into a parallel timeline from step K."""
        restored_state = self.rewind_to_step(step_index)
        branched_events = copy.deepcopy(self.events[:step_index])
        self.branches[branch_name] = branched_events
        self._persist()
        return restored_state

    def export_mermaid_timeline(self) -> str:
        """Generate a Mermaid timeline diagram of the full trajectory."""
        lines = [
            "timeline",
            "    title Trajektoria Wykonania (DARWIN-REPLAY 2027)",
        ]
        for evt in self.events:
            lines.append(f"    section Krok {evt.step_index}: {evt.stage_name.upper()}")
            lines.append(f"        {evt.agent_name} : {evt.description}")
        return "\n".join(lines)

    def _persist(self) -> Path:
        """Save the full trajectory and branches to disk."""
        file_path = self.memory_dir / "timeline_replay.json"
        data = {
            "events_count": len(self.events),
            "branches_count": len(self.branches),
            "events": [e.model_dump(mode="json") for e in self.events],
            "branches": {
                b: [e.model_dump(mode="json") for e in evts]
                for b, evts in self.branches.items()
            },
        }
        file_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return file_path
