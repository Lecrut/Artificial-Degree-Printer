"""Tic-Tac-Toe environment implementing standard game logic."""
from typing import List, Tuple, Dict, Any
import numpy as np

class TicTacToeEnv:
    """A tabular Tic-Tac-Toe environment returning numpy state arrays.

    States are encoded as a 3x3 numpy array where:
    -1 represents an empty cell,
     0 represents the 'O' player (often opponent/baseline),
     1 represents the 'X' player (the agent to be trained).
    """
    BOARD_SIZE: int = 3

    def __init__(self, board_size: int=3) -> None:
        """Initialize environment with an empty board.

    Args:
        board_size: The dimension of the square board (default is 3x3).
    """
        self._board = np.full((board_size, board_size), -1, dtype=np.int8)
        self._turn: int = -1

    def reset(self) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Reset the environment to the initial empty state.

    Returns:
        A tuple of (obs, info) where obs is the 3x3 numpy array and
turn is a dict with keys 'turn' and 'winner'.
    """
        self._board = np.full((self.BOARD_SIZE, self.BOARD_SIZE), -1, dtype=np.int8)
        self._turn = -1
        return (self._board.copy(), {'turn': self._turn, 'winner': None})

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """Execute the given action in the environment.

        Args:
            action: An integer index (0-8) representing the board cell to play.

        Returns:
            A tuple containing:
            - next_state: The updated 3x3 numpy array of the board.
            - reward: Float indicating the outcome (+1 for win, -1 for loss, 0 otherwise).
            - terminated: Boolean flag set if the game has ended in a win or loss.
            - truncated: Boolean flag set if the game has ended in a draw.
            - info: Dictionary containing metadata (e.g., winner, current turn).
        """
        if not 0 <= action < 9:
            raise ValueError(f'Action must be an integer between 0 and 8, got {action}')
        cell_idx = int(action)
        if self._board.ravel()[cell_idx] != -1:
            raise AssertionError('Tried to play on an occupied square.')
        self._board.ravel()[cell_idx] = self._turn
        winner, terminated, truncated = self._is_terminal()
        if terminated:
            reward = 1.0 if winner == -1 else -1.0
        else:
            reward = 0.0
        next_state = self._board.copy()
        info = {'turn': self._turn, 'winner': winner, 'terminated': terminated, 'truncated': truncated}
        self._turn = 0 if self._turn == -1 else -1
        return (next_state, reward, terminated, truncated, info)

    def get_legal_moves(self, player: int) -> List[int]:
        """Return a list of legal move indices for the current game state.

    Args:
        player: Argument kept for API compatibility but not used in logic,
                as legality depends only on empty cells on the board.

    Returns:
        A list of integers representing valid board indices (0-8).
    """
        return [i for i in range(9) if self._board.ravel()[i] == -1]

    def _is_terminal(self) -> Tuple[int, bool, bool]:
        """Check if the game has ended and determine the winner.

    Returns:
        A tuple of (winner_index, terminated_flag, truncated_flag).
        - winner_index: -1 for X win, 0 for O win, None for draw/ongoing.
        - terminated_flag: True if there is a winner.
        - truncated_flag: True if it's a draw.
    """
        lines = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]]
        x_won = False
        o_won = False
        for line in lines:
            vals = [self._board[line[0] // 3, line[0] % 3], self._board[line[1] // 3, line[1] % 3], self._board[line[2] // 3, line[2] % 3]]
            if vals[0] != -1 and vals[0] == vals[1] == vals[2]:
                if vals[0] == -1:
                    x_won = True
                elif vals[0] == 0:
                    o_won = True
        terminated = x_won or o_won
        winner = None
        if terminated:
            if x_won:
                winner = -1
            elif o_won:
                winner = 0
        truncated = False
        empty_count = np.sum(self._board == -1)
        if not terminated and empty_count == 0:
            truncated = True
        return (winner, terminated, truncated)

    @staticmethod
    def _check_win(board: np.ndarray) -> bool:
        """Check if the board has a winning line for any player.

Returns:
    True if there is a win, False otherwise.
"""
        lines = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]]
        for line in lines:
            vals = [board[i // 3, i % 3] for i in line]
            if vals[0] != -1 and vals[0] == vals[1] == vals[2]:
                return True
        return False

def _is_terminal(self) -> Tuple[int, bool, bool]:
    """Check if the game has ended and determine the winner.

    Returns:
        A tuple of (winner_index, terminated_flag, truncated_flag).
        - winner_index: 1 for X win, 0 for O win, None for draw/ongoing.
        - terminated_flag: True if X wins.
        - truncated_flag: True if it's a draw.
    """
    import collections
    counts = collections.Counter(tuple(self._board.ravel()))
    x_count = counts.get(-1, 0)
    o_count = counts.get(0, 0)
    empty_count = np.sum(self._board == -1)
    terminated = x_count > 4
    truncated = empty_count == 0
    winner = None
    if terminated:
        winner = -1
    return (winner, terminated, truncated)

@staticmethod
def _check_win(board: np.ndarray) -> bool:
    """Check if the board has a winning line for any player.

    Returns:
        True if there is a win, False otherwise.
    """
    lines = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]]
    for line in lines:
        if all((board[i] == board[0] and board[i] != -1 for i in line)):
            return True
    return False
