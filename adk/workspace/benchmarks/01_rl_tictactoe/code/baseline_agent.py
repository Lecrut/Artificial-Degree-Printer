"""Implements the random baseline agent that selects uniformly from valid moves."""
import numpy as np
from environment import TicTacToeEnv

class RandomAgent:
    """A dummy agent that chooses a legal move at random for baseline comparison."""

    def __init__(self, env: TicTacToeEnv) -> None:
        """Initialize the random agent.

        Args:
            env: The Tic-Tac-Toe environment instance. Stored to query valid actions.
        """
        self.env = env

    def act(self, state: np.ndarray) -> int:
        """Select a valid action uniformly at random from the legal moves in ``state``.

        Args:
            state: Current board observation (numpy array of shape (9,)).

        Returns:
            action: Integer index in [0, 8] corresponding to an empty cell on the board.
        """
        # Empty cells are represented by -1
        empty_indices = np.where(state == -1)[0]
        return int(np.random.choice(empty_indices))
