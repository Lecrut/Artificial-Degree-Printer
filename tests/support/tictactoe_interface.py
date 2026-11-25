"""The interface of a small tic-tac-toe environment, the module many tests plan around."""

from __future__ import annotations

ENV_INTERFACE = '''"""Game environment."""
BOARD_SIZE: int = 9


class TicTacToeEnv:
    """Board and rules."""

    def __init__(self, seed: int) -> None:
        """Create an empty board."""
        self.board = [0] * BOARD_SIZE

    def step(self, action: int) -> tuple[list[int], float, bool]:
        """Return (board, reward, done)."""
        return self.board, 0.0, False
'''
