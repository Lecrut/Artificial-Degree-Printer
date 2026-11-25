"""The state of a run (queue and counters) a re-plan test starts from."""

from __future__ import annotations

from adk.orchestration.common import _RunState


def _state(tasks: list[dict]) -> _RunState:
    return _RunState(user_prompt="p", max_retries=2, multi_cycle_waves=True, tasks=tasks)
