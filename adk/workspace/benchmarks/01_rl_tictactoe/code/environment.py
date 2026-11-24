"""Implements the Tic-Tac-Toe game logic and environment interface compatible with standard reinforcement learning patterns."""
from typing import Tuple, Dict, Any, Optional
import numpy as np
BOARD_SIZE: int = 3
STATE_SPACE_SIZE: int = 19683
ACTION_SPACE_SIZE: int = 9
PLAYER_X: int = 1
PLAYER_O: int = -1
REWARD_WIN: float = 1.0
REWARD_DRAW: float = 0.0
REWARD_LOSS: float = -1.0

class TicTacToeEnv:
    """A deterministic Tic-Tac-Toe environment following OpenAI Gymnasium conventions.

    States are represented as 1D numpy arrays of shape (9,) containing integers
    encoding the board: 0 for empty, 1 for Player X, -1 for Player O.
    Actions are integers in [0, 8] representing the cell index on the flattened board.
    """

    def __init__(self) -> None:
        """Initialize the environment with an empty board and no current player."""
        self.board: np.ndarray = np.zeros(BOARD_SIZE ** 2, dtype=int)
        self.current_player: int = PLAYER_X

    def reset(self, seed: Optional[int]=None) -> np.ndarray:
        """Reset the environment to the initial state.

Initializes the board to all zeros (empty). The game always starts with Player X.

Returns:
    np.ndarray of shape (9,), the initial board state (all zeros).
"""
        self.board = np.zeros(BOARD_SIZE ** 2, dtype=int)
        self.current_player = PLAYER_X
        return self.board.copy()

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """Execute one environment step.

Args:
    action: int in [0, 8]. The cell index where the current player places their mark.

Returns:
    Tuple containing:
        - next_obs: np.ndarray of shape (9,), the board state after the move.
        - reward: float. Reward for the *current* player (1 for win, -1 for loss, 0 for draw).
        - terminated: bool. True if the game has ended (win/loss/draw).
        - truncated: bool. False. Tic-Tac-Toe does not have time limits.
        - info: dict with keys:
            - 'player': int, the next player to move (or 0 if terminated).
            - 'legal_actions': list[int], valid actions in the new state.

Raises:
    ValueError: If the action is out of bounds or the cell is already occupied.
"""
        if not 0 <= action < BOARD_SIZE ** 2:
            raise ValueError(f'Action {action} out of bounds. Valid range is [0, {BOARD_SIZE ** 2 - 1}].')
        if self.board[action] != 0:
            raise ValueError(f'Action {action} invalid: cell already occupied.')
        self.board[action] = self.current_player
        next_player: int = -self.current_player
        win, draw = _check_terminal(self.board)
        terminated: bool = win or draw
        truncated: bool = False
        if win:
            current_reward = REWARD_WIN
        elif draw:
            current_reward = REWARD_DRAW
        else:
            current_reward = 0.0
            next_player = next_player
        if terminated:
            next_player = 0
        legal_actions: list[int] = [a for a in range(BOARD_SIZE ** 2) if self.board[a] == 0]
        info: Dict[str, Any] = {'player': next_player, 'legal_actions': legal_actions}
        return (self.board.copy(), current_reward, terminated, truncated, info)

def _check_terminal(board: np.ndarray) -> Tuple[bool, bool]:
    """Check if the game is won or drawn.

    Args:
        board: np.ndarray of shape (9,).

    Returns:
        Tuple (win, draw)."""
    win = False
    draw = False
    lines = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]]
    for line in lines:
        a, b, c = line
        if board[a] != 0 and board[a] == board[b] == board[c]:
            win = True
            break
    if not win and np.all(board != 0):
        draw = True
    return (win, draw)
