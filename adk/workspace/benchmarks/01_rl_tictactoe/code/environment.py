"""Implements the Tic-Tac-Toe game logic and a Gymnasium-compatible wrapper for interaction."""
from typing import Tuple, Dict, Any
import numpy as np
import gymnasium as gym

class TicTacToeEnv(gym.Env):
    """A standard 3x3 Tic-Tac-Toe environment compatible with the Gymnasium API."""

    def __init__(self) -> None:
        """Initialize the environment. Sets up spaces and internal state variables."""
        self._board: np.ndarray = np.zeros(9, dtype=np.int8)
        self.current_player: int = 1
        self._terminated: bool = False
        self._truncated: bool = False
        self.observation_space = gym.spaces.Box(low=0, high=2, shape=(9,), dtype=np.int8)
        self.action_space = gym.spaces.Discrete(9)

    def reset(self, seed: int | None=None, options: Dict[str, Any] | None=None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Reset the environment to the initial state."""
        self._board[:] = 0
        self.current_player = 1
        self._terminated = False
        self._truncated = False
        obs = self._board.copy()
        info = {'current_player': self.current_player}
        return (obs, info)

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """Execute one time step in the environment."""
        valid_action = self._board[action] == 0
        if not valid_action:
            return (self._board.copy(), 0.0, False, False, {'valid_action': False, 'winner': None, 'current_player': self.current_player})
        if self._terminated or self._truncated:
            return (self._board.copy(), 0.0, False, False, {'valid_action': True, 'winner': None, 'current_player': self.current_player})
        self._board[action] = self.current_player
        done, reward, info = self._check_terminal_state()
        self.current_player = 3 - self.current_player
        return (self._board.copy(), reward, done, self._truncated, info)

    def _check_terminal_state(self) -> Tuple[bool, float, Dict[str, Any]]:
        """Internal helper to check win/loss/draw and return status."""
        winner = None
        win_patterns = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]]
        for pattern in win_patterns:
            if self._board[pattern[0]] != 0 and self._board[pattern[0]] == self._board[pattern[1]] == self._board[pattern[2]]:
                winner = self._board[pattern[0]]
                break
        if winner is not None:
            reward = 1.0 if winner == self.current_player else -1.0
            return (True, reward, {'valid_action': True, 'winner': winner, 'current_player': 3 - self.current_player})
        if np.sum(self._board) > 0 and np.all(self._board != 0):
            reward = 0.0
            return (False, reward, {'valid_action': True, 'winner': None, 'current_player': 3 - self.current_player})
        return (False, 0.0, {'valid_action': True, 'winner': None, 'current_player': 3 - self.current_player})

class RandomAgent:
    """A simple agent that selects a random valid action from the current state."""

    def select_action(self, state: np.ndarray) -> int:
        """Select a valid move randomly from the available empty cells."""
        available_actions = list(np.where(state == 0)[0])
        if not available_actions:
            return -1
        action = np.random.choice(available_actions)
        return int(action)
