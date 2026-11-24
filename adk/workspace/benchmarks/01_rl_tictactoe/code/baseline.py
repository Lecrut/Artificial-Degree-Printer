"""Provides a random agent that selects uniformly from available legal moves for comparison purposes."""
import numpy as np

class RandomAgent:
    """A baseline opponent that picks a valid move at random."""

    def __init__(self) -> None:
        """Initialize the agent with no internal state.

    The agent is stateless; `get_action` relies entirely on the provided
    `valid_moves` to determine its output. This ensures the baseline is
    purely random and unbiased by history or previous games.
    """
        self._rng = np.random.default_rng()

    def get_action(self, state: np.ndarray, valid_moves: list[int]) -> int:
        """Select a uniformly random legal move from `valid_moves`.

    Args:
        state: The current board state (unused, included for interface
            compatibility with other agents). Should be a 3x3 numpy array.
        valid_moves: A list of integers representing the indices (0-8) of
            cells on the board that are currently empty and allow a legal move.

    Returns:
        An integer representing the index of the chosen move. The value
        will always be an element of `valid_moves`.

    Edge cases:
        - If `valid_moves` is empty (board full), raises ValueError as this
          indicates an invalid call during a non-terminal state or improper
          usage. In proper play, evaluation stops before such calls.
    """
        if len(valid_moves) == 0:
            raise ValueError('No valid moves available; board is full.')
        move_idx = self._rng.choice(len(valid_moves))
        return valid_moves[move_idx]
