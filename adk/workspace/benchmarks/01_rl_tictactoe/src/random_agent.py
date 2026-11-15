"""Baselines and simple agents for comparison."""
import random
from typing import Callable

class RandomPlayerAgent:
    """A baseline agent that plays uniformly at random."""

    def __init__(self, seed: int=42) -> None:
        """Initialize the random agent with a specific seed.

    Args:
        seed: Random seed for reproducibility (default 42).
    """
        self.seed = seed
        self.rng = random.Random(seed)

    def reset(self, state: tuple[int]) -> None:
        """Reset the agent's internal state.

    Args:
        state: The current game state (ignored as random agent has no memory).
    """
        self.rng = random.Random(self.seed)

    def get_move(self, state: tuple[int]) -> int:
        """Return a uniformly random available move.

        Args:
            state: The current game state (tuple of board coordinates).

        Returns:
            An integer index representing the chosen move coordinate,
            selected randomly from all valid moves for Tic-Tac-Toe.
        """
        valid_moves = [i for i, val in enumerate(state) if val == 0]
        if not valid_moves:
            raise ValueError('No valid moves available in the given state.')
        return self.rng.choice(valid_moves)
