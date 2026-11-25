"""Implements a baseline opponent that selects uniformly at random from available moves using only the provided state and RNG."""
from typing import Any
import numpy as np

class RandomAgent:
    """A baseline agent that chooses moves uniformly at random, useful for evaluating the learning performance of a Q-Learning agent."""

    def __init__(self, rng: np.random.Generator | None=None) -> None:
        """Initializes the RandomAgent with the provided RNG. The agent makes no decisions internally and relies on the passed 'rng' during action selection. If an external RNG is not needed (e.g., for state storage), it remains unused."""
        self.rng = rng

    def act(self, state: dict, rng: np.random.Generator) -> int:
        """Selects a valid move for the player corresponding to 'state'. It uses the provided 'rng' object to generate the random number; if no valid moves exist, it returns -1. Returns an integer index of the cell to move into."""
        valid_moves = [i for i in state.keys() if state[i] == 0 or state[i] is None]
        if not valid_moves:
            return -1
        choice: int = rng.choice(valid_moves)
        return int(choice)
