"""Baseline opponent implementations."""
from typing import List, Tuple
import random

class RandomAgent:
    """Plays uniformly random valid moves."""

    def act(self, state: Tuple[int, ...], valid_actions: List[int]) -> int:
        """Return a random valid action.

    >>> valid = [0, 1]
    >>> agent = RandomAgent()
    >>> # Just ensures it returns one of the valid actions
    >>> res = agent.act((0,)*9, valid)
    >>> res in valid
    True
    """
        return random.choice(valid_actions)
