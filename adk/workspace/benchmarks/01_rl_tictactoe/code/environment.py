"""Tic-Tac-Toe Environment implementation."""
from typing import List, Tuple
import numpy as np

class TicTacToeEnv:
    """A simple 3x3 Tic-Tac-Toe environment.

    State is a tuple of 9 integers: -1 (O), 0 (empty), 1 (X).
    """

    def __init__(self) -> None:
        """Initialize empty board."""
        self._board: Tuple[int, ...] = tuple((0,) * 9)

    def reset(self) -> Tuple[int, ...]:
        """Reset environment and return initial state.

>>> env = TicTacToeEnv()
>>> state = env.reset()
>>> len(state) == 9 and all(s == 0 for s in state)
True
"""
        self._board: Tuple[int, ...] = tuple((0,) * 9)
        return self._board

    def step(self, action: int, player: int) -> Tuple[Tuple[int, ...], float, bool]:
        """Execute action for the given player.

Args:
    action: Index 0-8 on the board.
    player: 1 for X, -1 for O.

Returns:
    Tuple of (next_state, reward, done).

>>> env = TicTacToeEnv()
>>> env.reset()
>>> next_s, r, d = env.step(4, 1)
>>> next_s[4] == 1
True
"""
        old_state: Tuple[int, ...] = self._board
        available_moves: List[int] = [i for i, c in enumerate(old_state) if c == 0]
        if action not in available_moves:
            raise ValueError(f'Invalid action {action} for state {old_state}')
        new_board: Tuple[int, ...] = list(old_state)
        new_board[action] = player
        self._board = tuple(new_board)
        reward: float = 0.0
        done: bool = not any((cell == 0 for cell in self._board))
        return (self._board, reward, done)

    def get_valid_actions(self, state: Tuple[int, ...]) -> List[int]:
        """Return list of valid move indices."""
        return [i for i, cell in enumerate(state) if cell == 0]

    def is_terminal(self, state: Tuple[int, ...]) -> bool:
        """Check if state is terminal (win/loss/draw)."""
        wins: bool = self.check_win(state, 1) or self.check_win(state, -1)
        draw: bool = not any((cell == 0 for cell in state))
        return wins or draw

    def check_win(self, state: Tuple[int, ...], player: int) -> bool:
        """Check if `player` has won.

Args:
    state: 3x3 board as tuple of 9 integers (-1 for O, 0 empty, 1 for X).
    player: 1 for X, -1 for O.

Returns:
    True if `player` controls all cells in any winning line, False otherwise.
"""
        winning_lines: List[Tuple[int, int, int]] = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
        for line in winning_lines:
            if all((cell == player for cell, idx in zip(state, line))):
                return True
        return False
