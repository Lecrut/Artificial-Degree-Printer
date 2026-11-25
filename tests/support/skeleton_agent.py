"""The agent that answers a skeleton task, as the symbol-edit tests need it."""

from __future__ import annotations

SKELETON_AGENT = (
    "class Agent:\n"
    "    def __init__(self, alpha: float) -> None:\n"
    "        raise NotImplementedError\n\n"
    "    def act(self, state: tuple) -> int:\n"
    "        \"\"\"Returns the chosen action index.\"\"\"\n"
    "        raise NotImplementedError\n"
)
