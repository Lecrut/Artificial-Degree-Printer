"""Finite-state Tic-Tac-Toe environment adhering to the Gymnasium API."""
from __future__ import annotations
import gymnasium as gym
from typing import Tuple, List, Optional
import numpy as np
BOARD_SIZE: int = 9
MAX_PLAYERS: List[int] = [1, -1]
WINNING_LINES: Tuple[Tuple[int, ...], ...] = ((0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6))

class TicTacToeEnv(gym.Env):
    """
    A tabular Tic-Tac-Toe environment using the Gymnasium interface.

    The board is flattened to a 1D array of length 9 (indices 0-8).
    Player X (value +1) always moves first. Player O (value -1) moves second.
    Rewards are symmetric zero-sum: +1 for winning, -1 for losing, 0 for draw.
    """
    render_mode: 'object'
    metadata = {'render_modes': ['ansi']}
    observation_space: gym.spaces.Box
    action_space: gym.spaces.Discrete
    _board: np.ndarray
    _current_player: int
    _terminated: bool

    def __init__(self, render_mode: Optional[str]=None) -> None:
        """
    Initialize the environment.

    Args:
        render_mode: Optional rendering mode (not used in this stub).
    """
        self._board: np.ndarray = np.zeros(BOARD_SIZE, dtype=int)
        self._current_player: int = 1
        self._terminated: bool = False
        self.observation_space = gym.spaces.Box(low=0, high=9, shape=(BOARD_SIZE,), dtype=np.int32)
        self.action_space = gym.spaces.Discrete(BOARD_SIZE)

    def reset(self, seed: Optional[int]=None, options: Optional[dict]=None) -> Tuple[np.ndarray, dict]:
        """
    Reset the environment to the initial empty state.

    Args:
        seed: Optional random seed.
        options: Additional options (unused).

    Returns:
        observation: The initial board state as a numpy array.
        info: A dictionary containing auxiliary information including 'legal_moves'.
    """
        if seed is not None:
            np.random.seed(seed)
        self._board[:] = 0
        self._current_player = 1
        self._terminated = False
        return (self._board, {'legal_moves': self.get_valid_actions()})

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, dict]:
        """
    Execute one time step in the environment.

    Args:
        action: An integer in [0, 8] representing the grid index to place a mark.

    Returns:
        observation: The new board state.
        reward: +1 if the current player wins, -1 if they lose, 0 otherwise.
        terminated: True if the game is over (win/loss/draw).
        truncated: Always False in standard Tic-Tac-Toe unless hard limits are added.
        info: Auxiliary info containing valid actions for the next turn.

    Raises:
        ValueError: If the action is invalid (occupied or out of bounds).
    """
        if not self._terminated:
            if action in self.get_valid_actions():
                idx = action
                if self._current_player == 1:
                    self._board[idx] = 1
                else:
                    self._board[idx] = -1
                terminated, truncated, info = self._check_game_status()
                if terminated:
                    pass
                else:
                    self._current_player = -self._current_player
                return (self._board, info.get('reward', 0.0), terminated, truncated, info)
        raise ValueError(f'Invalid action {action}.')

    def get_valid_actions(self) -> List[int]:
        """
    Return a list of valid (empty) actions available in the current state.

    Returns:
        A list of integers representing indices of empty cells on the board.
    """
        return [i for i in range(BOARD_SIZE) if self._board[i] == 0]

    def _check_win(self, player: int) -> bool:
        """
Check if a specific player has won. Uses precomputed winning lines.

Args:
    player: The player ID (+1 or -1) to check for.

Returns:
    True if the player has formed a line, False otherwise.
"""
        return any((all((self._board[i] == player for i in line)) for line in WINNING_LINES))

    def _check_game_status(self) -> Tuple[bool, bool, dict]:
        """
    Check if the game is terminated (win or draw) and return status info.

    Returns:
        terminated: True if the game is over, False otherwise.
        truncated: Always False for Tic-Tac-Toe.
        info: Dictionary containing 'reward' (+1/-1/0), 'winner' (1/-1/0) and 'valid_moves'.
    """
        reward = 0.0
        winner = 0
        terminated = False
        if self._check_win(1):
            winner = 1
            reward = 1.0
            terminated = True
        elif self._check_win(-1):
            winner = -1
            reward = -1.0
            terminated = True
        if not terminated and all((x != 0 for x in self._board)):
            terminated = True
            reward = 0.0
            winner = 0
        info: dict = {'reward': reward, 'winner': winner, 'valid_moves': self.get_valid_actions()}
        return (terminated, False, info)

def _reset_game(self) -> Tuple[bool, bool, dict]:
    """
    Check if the game is terminated (win or draw) and return status info.

    Returns:
        terminated: True if the game is over, False otherwise.
        truncated: Always False for Tic-Tac-Toe.
        info: Dictionary containing 'winner' (1/ -1 / 0) and 'valid_moves'.
    """
    winner = 0
    if self._check_win(1):
        winner = 1
    elif self._check_win(-1):
        winner = -1
    terminated = winner != 0 or all((x != 0 for x in self._board))
    info: dict = {'winner': winner, 'valid_moves': self.get_valid_actions()}
    return (terminated, False, info)
