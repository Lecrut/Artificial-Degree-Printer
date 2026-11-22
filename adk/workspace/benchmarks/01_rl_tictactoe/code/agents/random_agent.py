"""Baseline random agent for Tic-Tac-Toe."""
from __future__ import annotations
import numpy as np
import random
from typing import List

class RandomAgent:
    """
    A baseline agent that selects uniformly at random from valid actions.

    This agent serves as a performance floor. It does not learn; it chooses
    any legal move with equal probability.
    """
    name: str = 'random_agent'

    def act(self, state: np.ndarray, valid_actions: List[int]) -> int:
        """
    Select a random action from the provided list of valid actions.

    Args:
        state: The current observation (board state). Unused for logic,
               kept for interface consistency with QLearningAgent.
        valid_actions: A list of integers representing legal move indices.

    Returns:
        An integer representing the selected action index, drawn uniformly
        from `valid_actions`.

    Edge cases:
        - If `valid_actions` is empty (e.g., game already over), raises
          IndexError. Callers should check termination status before calling.
    """
        if not valid_actions:
            raise IndexError('No valid actions available')
        return random.choice(valid_actions)
