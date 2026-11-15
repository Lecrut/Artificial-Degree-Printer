"""
Tic-Tac-Toe Environment for Q-Learning experiments.
Provides state representation, game logic (win/draw/loss), and interaction interface.
"""
from dataclasses import dataclass
import numpy as np
from typing import Tuple, List

class TicTacToeEnv:
    """Environment for 3x3 Tic-Tac-Toe game."""

    @staticmethod
    def get_symbol() -> int:
        """Return the value for player X."""
        return 0

    @staticmethod
    def get_empty() -> int:
        """Return the value for an empty cell."""
        return 1

    def __init__(self, max_turns: int=-1, use_terminal_value: bool=True) -> None:
        self.max_turns = max_turns
        self.use_terminal_value = use_terminal_value
        self.state: np.ndarray = np.zeros(9, dtype=np.int64)
        self.turn = 0
        self.game_over = False
        self.winner: int = -1

    def reset(self) -> Tuple[np.ndarray, int]:
        """
    Reset the environment to initial state.

    Returns:
        state (np.ndarray): 1D array of shape (9,). Zeroed board with empty cells=1.
        reward (int): 0.
    """
        self.state = np.zeros(9, dtype=np.int64)
        self.turn = 0
        self.game_over = False
        self.winner = -1
        return (self.state.copy(), 0)

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, dict]:
        """
    Execute a single turn.

    Args:
        action (int): Board index (0-8).

    Returns:
        state (np.ndarray): 1D array of shape (9,).
        reward (float): Immediate reward.
        done (bool): True if game over.
        info (dict): Game info.
    """
        if action < 0 or action >= 9:
            raise ValueError(f'Invalid action {action}.')
        flat_state = self.state.copy()
        cell_idx = int(action)
        cell_val = flat_state[cell_idx]
        empty_val = TicTacToeEnv.get_empty()
        if not np.array_equal(cell_val, empty_val):
            raise ValueError(f'Cell {cell_idx} is already occupied.')
        flat_state[cell_idx] = 0
        self.state[:] = flat_state
        self.turn += 1
        if self._check_game_over():
            done = True
            self.game_over = True
            winner_id = 0 if self._check_winner_line(0) else -1
            reward = 1.0 if winner_id == 0 and self.use_terminal_value else 0.0
            info = {'state': self.state.copy(), 'winner': 'X' if winner_id == 0 else '-', 'turn': self.turn}
            return (self.state.copy(), reward, done, info)
        empty_cells = [i for i in range(9) if self.state[i] == empty_val]
        if not empty_cells:
            done = True
            reward = 0.0
            info = {'state': self.state.copy(), 'winner': '-', 'turn': self.turn}
            return (self.state.copy(), reward, done, info)
        np.random.seed(self.turn * 2)
        opp_idx = np.random.choice(empty_cells)
        flat_state[opp_idx] = 1
        self.state[:] = flat_state
        if self._check_game_over():
            done = True
            self.game_over = True
            winner_id = 1 if self._check_winner_line(1) else -1
            reward = 1.0 if winner_id == 1 and self.use_terminal_value else 0.0
            info = {'state': self.state.copy(), 'winner': 'O' if winner_id == 1 else '-', 'turn': self.turn}
            return (self.state.copy(), reward, done, info)
        info = {'state': self.state.copy(), 'winner': '-', 'turn': self.turn}
        reward = 0.0
        return (self.state.copy(), reward, False, info)

    def get_state_key(self) -> np.ndarray:
        """
    Convert the board state into a flat key for hashing or feature extraction.

    Returns:
        key (np.ndarray): Flattened representation of the 3x3 board.
    """
        return self.state.flatten()

    def is_game_over(self) -> bool:
        """
    Check if the current game state is over (win or draw).

    Returns:
        is_over (bool): True if game has ended, False otherwise.
    """
        return self.game_over

    def _place_piece(self, player: int, action: int) -> bool:
        """
    Place a piece at the given action index.

    Args:
        player (int): Player ID (0 or 2).
        action (int): Index in the flattened state array (0-8).

    Returns:
        bool: True if successful.
    """
        cell_idx = int(action)
        if not 0 <= cell_idx < 9:
            raise ValueError(f'Invalid action {cell_idx}.')
        flat_state = self.state.copy()
        if not np.array_equal(flat_state[cell_idx], TicTacToeEnv.get_empty()):
            raise ValueError(f'Cell {cell_idx} is already occupied.')
        flat_state[cell_idx] = player
        return True

    def _check_game_over(self) -> bool:
        """
    Check if the game is over (win or draw).

    Returns:
        is_over (bool): True if win/draw detected.
    """
        flat_state = self.state.copy()
        occupied_count = int((flat_state != TicTacToeEnv.get_empty()).sum())
        if occupied_count == 9:
            return True
        wins = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]]
        for combo in wins:
            a, b, c = flat_state[combo]
            if a != TicTacToeEnv.get_empty() and b == a and (c == a):
                return True
        return False

    def _check_winner_line(self, player: int) -> bool:
        """
    Check if a specific player has won.

    Args:
        player (int): Player ID (0 or 2).

    Returns:
        is_winner (bool): True if win detected.
    """
        flat_state = self.state.copy()
        wins = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]]
        for combo in wins:
            a, b, c = flat_state[combo]
            if a == player and b == player and (c == player):
                return True
        return False

def __init__(self, max_turns: int=-1, use_terminal_value: bool=True) -> None:
    """
Initialize the Tic-Tac-Toe environment.

Args:
    max_turns: Maximum number of turns. If -1, game continues until win/draw.
    use_terminal_value: If True, terminal rewards are 0. If False, +1/-1 for winner.
"""
    self.max_turns = max_turns
    self.use_terminal_value = use_terminal_value
    self.state: np.ndarray = np.zeros(9, dtype=np.int64)
    self.turn = 0
    self.game_over = False
    self.winner: int = -1

def reset(self) -> Tuple[np.ndarray, int]:
    """
Reset the environment to initial state.

Returns:
    state (np.ndarray): 1D array of shape (9,). Zeroed board with empty cells=1.
    reward (int): 0.
"""
    self.state = np.zeros(9, dtype=np.int64)
    self.turn = 0
    self.game_over = False
    self.winner = -1
    return (self.state.copy(), 0)

def step(self, action: int) -> Tuple[np.ndarray, float, bool, dict]:
    """
Execute a single turn.

Args:
    action (int): Board index (0-8).

Returns:
    state (np.ndarray): 1D array of shape (9,).
    reward (float): Immediate reward.
    done (bool): True if game over.
    info (dict): Game info.
"""
    if action < 0 or action >= 9:
        raise ValueError(f'Invalid action {action}.')
    flat_state = self.state.copy()
    cell_idx = int(action)
    cell_val = flat_state[cell_idx]
    empty_val = TicTacToeEnv.get_empty()
    if not np.array_equal(cell_val, empty_val):
        raise ValueError(f'Cell {cell_idx} is already occupied.')
    flat_state[cell_idx] = 2
    self.state[:] = flat_state
    self.turn += 1
    if self._check_game_over():
        done = True
        self.game_over = True
        current_win = self._check_winner_line(2) or self._check_winner_line(0)
        if not current_win:
            is_draw = self.state.sum() == 9 and self.turn >= 5
            done = is_draw
            reward = 0.0 if is_draw else 0.0
        else:
            winner_id = 2 if current_win else 0
            reward = 1.0 if winner_id == 2 and self.use_terminal_value else -1.0 if winner_id == 0 and self.use_terminal_value else 0.0
        info = {'state': self.state.copy(), 'winner': 1 if winner_id == 1 else 2 if winner_id == 2 else 0, 'turn': self.turn}
        return (self.state.copy(), reward, done, info)
    empty_cells = [i for i in range(9) if self.state[i] == empty_val]
    if not empty_cells:
        done = True
        reward = 0.0
        info = {'state': self.state.copy(), 'winner': -1, 'turn': self.turn}
        return (self.state.copy(), reward, done, info)
    np.random.seed(self.turn * 2)
    opp_idx = np.random.choice(empty_cells)
    flat_state[opp_idx] = 0
    self.state[:] = flat_state
    if self._check_game_over():
        done = True
        self.game_over = True
        winner_id = 2 if self._check_winner_line(2) else 0 if self._check_winner_line(0) else -1
        if winner_id == -1:
            reward = 0.0
        elif winner_id == 2:
            reward = -1.0 if self.use_terminal_value else 0.0
        else:
            reward = 1.0 if self.use_terminal_value else 0.0
        info = {'state': self.state.copy(), 'winner': 1 if winner_id == 1 else 2 if winner_id == 2 else 0, 'turn': self.turn}
        return (self.state.copy(), reward, done, info)
    info = {'state': self.state.copy(), 'winner': -1, 'turn': self.turn}
    reward = 0.0
    return (self.state.copy(), reward, False, info)

def get_state_key(self) -> np.ndarray:
    """
Convert the board state into a flat key for hashing or feature extraction.

Returns:
    key (np.ndarray): Flattened representation of the 3x3 board.
"""
    return self.state.flatten()

def is_game_over(self) -> bool:
    """
Check if the current game state is over (win or draw).

Returns:
    is_over (bool): True if game has ended, False otherwise.
"""
    return self.game_over

def _place_piece(self, player: int, action: int) -> bool:
    """
Place a piece at the given action index.

Args:
    player (int): Player ID (0 or 2).
    action (int): Index in the flattened state array (0-8).

Returns:
    bool: True if successful.
"""
    cell_idx = int(action)
    if not 0 <= cell_idx < 9:
        raise ValueError(f'Invalid action {cell_idx}.')
    flat_state = self.state.copy()
    if flat_state[cell_idx] != TicTacToeEnv.get_empty():
        raise ValueError(f'Cell {cell_idx} is already occupied.')
    flat_state[cell_idx] = player
    return True

def _check_game_over(self) -> bool:
    """
Check if the game is over (win or draw).

Returns:
    is_over (bool): True if win/draw detected.
"""
    flat_state = self.state.copy()
    occupied_count = int((flat_state != TicTacToeEnv.get_empty()).sum())
    if occupied_count == 9:
        return True
    wins = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]]
    for combo in wins:
        a, b, c = flat_state[combo]
        if a != TicTacToeEnv.get_empty() and b == a and (c == a):
            return True
    return False

def _check_winner_line(self, player: int) -> bool:
    """
Check if a specific player has won.

Args:
    player (int): Player ID (0 or 2).

Returns:
    is_winner (bool): True if win detected.
"""
    flat_state = self.state.copy()
    wins = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]]
    for combo in wins:
        a, b, c = flat_state[combo]
        if a == player and b == player and (c == player):
            return True
    return False
