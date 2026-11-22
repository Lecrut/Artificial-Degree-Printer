"""Implements the Tic-Tac-Toe game logic and a Gymnasium-compatible wrapper."""
import gymnasium as gym
from typing import Tuple, Optional
import numpy as np

class TicTacToeEnv(gym.Env):
    """A Gymnasium environment for the Game of Tic-Tac-Toe.
    
    The board is represented as a 1D array of size 9 (3x3 flattened), 
    where cells contain 0 (empty), 1 (player X), or -1 (player O).
    Player X always moves first.
    """
    render_mode: 'object'
    board_size: 'object'
    observation_space: 'object'
    action_space: 'object'
    metadata = {'render_modes': ['human', 'ansi']}

    def __init__(self, render_mode: Optional[str]=None):
        """Initialize the environment.

    Args:
        render_mode: Rendering mode string. Defaults to None (no rendering).
    """
        self.render_mode: str = render_mode or 'None'
        self.board_size: int = 9
        self.observation_space: gym.spaces.Box = gym.spaces.Box(low=0, high=2, shape=(9,), dtype=np.int8)
        self.action_space: gym.spaces.Discrete = gym.spaces.Discrete(9)
        self._board: np.ndarray = None

    def reset(self, seed: Optional[int]=None) -> Tuple[np.ndarray, dict]:
        """Resets the environment to the initial state.

    Args:
        seed: Optional random seed for reproducibility. Defaults to None.

    Returns:
        observation: The initial board state (np.ndarray of shape (9,) with dtype int8).
        info: Auxiliary diagnostic information (empty dict).
    """
        if seed is not None:
            np.random.seed(seed)
        self._board = np.zeros(self.board_size, dtype=np.int8)
        observation = self._board.copy()
        info = {}
        return (observation, info)

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, dict]:
        """Performs a single environment step.

    Args:
        action: An integer in [0, 8] representing the cell index to place a mark.

    Returns:
        observation: The new board state (np.ndarray).
        reward: Reward for the current player (+1 for win, 0 for draw, -1 for loss).
        terminated: Boolean indicating if the game has ended due to win or loss.
        truncated: Boolean indicating if the episode was truncated. Always False.
        info: Auxiliary diagnostic information including if the action was legal and whose turn it is.

    Raises:
        ValueError: If the action is invalid (cell already occupied).
    """
        current_player = 1 if self._board.sum() == 0 else -1
        next_player = -current_player
        info: dict = {}
        if action >= self.board_size:
            raise ValueError(f'Action {action} out of bounds. Valid actions are 0 to {self.board_size - 1}.')
        if self._board[action] != 0:
            info['legal_action'] = False
            info['turn'] = current_player
            return (self._board, 0.0, False, True, info)
        old_state = self._board.copy()
        self._board[action] = next_player
        new_state = self._board.copy()
        game_over = self._check_win(next_player) or len(old_state) == self.board_size - 1
        if game_over:
            win_loss_result = self._check_win(next_player)
            reward = 1.0 if win_loss_result else 0.0 if len(new_state) == self.board_size else -1.0
            terminated = True
            truncated = False
        else:
            reward = 0.0
            terminated = False
            truncated = False
        info['legal_action'] = True
        info['turn'] = current_player
        return (new_state, reward, terminated, truncated, info)

    def _check_win(self, player: int) -> bool:
        """Check if the specified player has won.

    Args:
        player: The player identifier (1 or -1).

    Returns:
        True if the player has three in a row, False otherwise.
    """
        rows = [self._board[i:i + 3] for i in range(0, 9, 3)]
        cols = [[self._board[j * 3 + i] for j in range(3)] for i in range(3)]
        diagonals = [[self._board[0], self._board[4], self._board[8]], [self._board[2], self._board[4], self._board[6]]]
        for row in rows:
            if player == 1 and np.all(row == 1):
                return True
            elif player == -1 and np.all(row == -1):
                return True
        for col in cols:
            if player == 1 and np.all(col == 1):
                return True
            elif player == -1 and np.all(col == -1):
                return True
        for diag in diagonals:
            if player == 1 and np.all(diag == 1):
                return True
            elif player == -1 and np.all(diag == -1):
                return True
        return False
