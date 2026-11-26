"""Provides a random baseline agent for Tic-Tac-Toe that selects uniformly from valid moves."""
from typing import List, Optional
import numpy as np

class RandomAgent:
    """A baseline agent that chooses uniformly at random from the set of valid actions."""

    def __init__(self) -> None:
        """Initializes the random baseline agent. No state is required as action selection depends only on the input list of valid actions.

    Args:
        self: The agent instance (implicit).
    """
        pass

    def choose_action(self, valid_actions: List[int], rng: Optional[np.random.Generator]=None) -> int:
        """Selects an action uniformly at random from `valid_actions`.

    Args:
        self: The agent instance (implicit).
        valid_actions: A list of integers representing valid move indices. This parameter is required.
        rng: An optional NumPy random generator for reproducibility. Defaults to None, which uses the global numpy random generator.

    Returns:
        int: An integer representing the chosen action index from `valid_actions`.

    Raises:
        ValueError: If `valid_actions` is empty, as no valid moves exist.
    """
        if rng is None:
            rng = np.random.default_rng()
        if len(valid_actions) == 1:
            return valid_actions[0]
        chosen_index = rng.integers(0, len(valid_actions))
        return valid_actions[chosen_index]
