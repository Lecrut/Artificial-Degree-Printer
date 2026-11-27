"""Provides a custom Tic-Tac-Toe Gymnasium environment where observations are integer state hashes compatible with direct Q-table indexing and deterministic opponent moves."""
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Tuple, Dict, Any, Optional
BOARD_SIZE: int = 3
NUM_ACTIONS: int = 9
PLAYER_X: int = 1
PLAYER_O: int = -1
DRAW_REWARD: float = 0.5
WIN_REWARD: float = 1.0
LOSS_REWARD: float = -1.0

class TicTacToeEnv(gym.Env):
    """A Tic-Tac-Toe environment implementing the Gymnasium API.

    The environment manages a 3x3 board. The agent plays as Player X (value 1). Actions are indices 0-8 corresponding to empty cells. The observation is an integer hash of the board state, suitable for direct Q-table indexing. Empty cells are 0, Player X is 1, and Player O is represented by base-3 digit 2 in the hash calculation."""
    observation_space: spaces.Discrete
    action_space: spaces.Discrete

    def __init__(self) -> None:
        """Initializes the environment. Sets up observation and action spaces."""
        super().__init__()
        self.observation_space = spaces.Discrete(pow(3, BOARD_SIZE * BOARD_SIZE))
        self.action_space = spaces.Discrete(NUM_ACTIONS)
        self.board: np.ndarray = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)

    def reset(self, seed: Optional[int]=None) -> Tuple[int, Dict[str, Any]]:
        """Resets the environment to the initial empty board state.

    Args:
        seed: Optional random seed for reproducibility.

    Returns:
        tuple: A tuple containing the initial observation (integer hash of empty board) and an info dict."""
        super().reset(seed=seed)
        self.board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)
        if seed is not None:
            self.np_random = np.random.default_rng(seed)
        return (self.get_state_hash(self.board), {})

    def step(self, action: int) -> Tuple[int, float, bool, bool, Dict[str, Any]]:
        """Processes one time step.

    Args:
        action: An integer 0-8 representing the chosen cell.

    Returns:
        tuple: (observation, reward, terminated, truncated, info)
            - observation: The integer hash of the new board state.
            - reward: Reward for the agent (+1 if win, -1 if loss, +0.5 if draw, 0 otherwise).
            - terminated: True if the game ended by win/loss/draw.
            - truncated: Always False (no time limit within an episode).
            - info: Dict containing 'valid_move' and 'winner' information."""
        valid_moves: list = self.get_valid_moves()
        if not isinstance(action, int) or action < 0 or action >= NUM_ACTIONS or (action not in valid_moves):
            obs: int = self.get_state_hash(self.board)
            return (obs, 0.0, False, False, {'valid_move': False})
        row: int = action // BOARD_SIZE
        col: int = action % BOARD_SIZE
        self.board[row, col] = PLAYER_X
        winner: Optional[int] = self._check_winner()
        if winner is not None:
            reward: float = WIN_REWARD if winner == PLAYER_X else LOSS_REWARD
            if winner == 0:
                reward = DRAW_REWARD
            return (self.get_state_hash(self.board), reward, True, False, {'valid_move': True, 'winner': winner})
        opp_moves: list = self._get_available_moves()
        if not opp_moves:
            return (self.get_state_hash(self.board), DRAW_REWARD, True, False, {'valid_move': True, 'winner': 0})
        try:
            if hasattr(self, 'np_random') and self.np_random is not None:
                opp_action: int = int(self.np_random.choice(opp_moves))
            else:
                import random
                opp_action: int = int(random.choice(opp_moves))
        except Exception:
            opp_action: int = opp_moves[0]
        r_opp: int = opp_action // BOARD_SIZE
        c_opp: int = opp_action % BOARD_SIZE
        self.board[r_opp, c_opp] = PLAYER_O
        winner = self._check_winner()
        if winner is not None:
            reward = WIN_REWARD if winner == PLAYER_X else LOSS_REWARD
            if winner == 0:
                reward = DRAW_REWARD
            return (self.get_state_hash(self.board), reward, True, False, {'valid_move': True, 'winner': winner})
        return (self.get_state_hash(self.board), 0.0, False, False, {'valid_move': True, 'winner': None})

    def get_state_hash(self, state: np.ndarray) -> int:
        """Computes the integer hash for a given numpy board array.

        Args:
            state: A 3x3 numpy array representing the board. Player O is encoded as value 2 in the base-3 expansion to avoid collisions with empty cells (0) and X (1).

        Returns:
            int: A unique integer identifier for the state."""
        flattened = state.flatten()
        val: int = 0
        for i, cell in enumerate(flattened):
            if cell == PLAYER_O:
                val += 2 * 3 ** i
            elif cell == PLAYER_X:
                val += 1 * 3 ** i
        return val

    def _get_available_moves(self) -> list:
        """Returns a list of available action indices (empty cells).

    Returns:
        list: List of integers 0-8 corresponding to empty cells."""
        return [i for i in range(NUM_ACTIONS) if self.board.flat[i] == 0]

    def _check_winner(self) -> Optional[int]:
        """Checks if there is a winner or if the board is full.

        Returns:
            Optional[int]: PLAYER_X (1) if X wins, PLAYER_O (-1) if O wins, 0 for draw, None if game continues."""
        for i in range(BOARD_SIZE):
            if np.sum(self.board[i, :]) == BOARD_SIZE * PLAYER_X:
                return PLAYER_X
            if np.sum(self.board[i, :]) == BOARD_SIZE * PLAYER_O:
                return PLAYER_O
        for j in range(BOARD_SIZE):
            if np.sum(self.board[:, j]) == BOARD_SIZE * PLAYER_X:
                return PLAYER_X
            if np.sum(self.board[:, j]) == BOARD_SIZE * PLAYER_O:
                return PLAYER_O
        if np.sum(np.diagonal(self.board)) == BOARD_SIZE * PLAYER_X:
            return PLAYER_X
        if np.sum(np.diagonal(np.fliplr(self.board))) == BOARD_SIZE * PLAYER_X:
            return PLAYER_X
        if np.sum(np.diagonal(self.board)) == BOARD_SIZE * PLAYER_O:
            return PLAYER_O
        if np.sum(np.diagonal(np.fliplr(self.board))) == BOARD_SIZE * PLAYER_O:
            return PLAYER_O
        if np.all(self.board != 0):
            return 0
        return None

    def get_valid_moves(self) -> list:
        """Returns the list of valid actions for the current state.

        Returns:
            list: List of integers representing available moves."""
        return self._get_available_moves()
