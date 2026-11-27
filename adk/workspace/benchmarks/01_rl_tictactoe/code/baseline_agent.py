"""Implements the random baseline player using standard library `random` module for deterministic reproducibility."""

from typing import List, Optional
import random


class RandomAgent:
    """A simple agent that chooses a legal move uniformly at random from the environment's valid moves."""
    _rng: random.Random

    def __init__(self, seed: Optional[int]) -> None:
        """Initializes the RandomAgent. Creates an instance-level random number generator seeded with the provided value to ensure deterministic reproducibility without affecting global state."""
        self._rng = random.Random(seed)

    def choose_action(self, state_hash: int, possible_moves: List[int]) -> int:
        """Selects one action from the allowed moves using the instance's random number generator.

        Args:
            state_hash: The integer hash of the current board state (unused by this agent but required for interface compatibility).
            possible_moves: A list of integers representing valid action indices available in the current state.

        Returns:
            int: A single action index chosen uniformly at random from `possible_moves`. If `possible_moves` is empty, raises ValueError."""
        if not possible_moves:
            raise ValueError("Possible moves list cannot be empty")
        return possible_moves[self._rng.randint(0, len(possible_moves) - 1)]
