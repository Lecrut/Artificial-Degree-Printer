"""
Tic-Tac-Toe environment for Q-Learning experiments.
"""
import numpy as np
from typing import Tuple, Optional
from enum import Enum

class Player(Enum):
    PLAYER_ONE: int = 1
    PLAYER_TWO: int = -1
    AI: int = 0

class TicTacToeEnv:

    def __init__(self, max_steps: int=9) -> None:
        """Initialize the environment with a maximum number of steps."""
        self.max_steps: int = max_steps
        self._state: np.ndarray | None = None
        self._current_player: Player = Player.PLAYER_ONE
        self._step_count: int = 0
        self.reset()

    def reset(self) -> np.ndarray:
        """
    Reset the environment to an empty board and return the initial state key.
    Returns a flat numpy array of shape (9,) representing the 3x3 grid.
    Values: -1=Empty, 0=AI, 1=Human.
    """
        self._state = np.zeros((9,), dtype=int)
        return self._state.copy()

    def step(self, action: int) -> Tuple[np.ndarray, float, bool]:
        """
    Execute a move for the AI (index 0..8), get next state, reward, and done flag.
    Args:
        action: Integer index of the cell to place 'AI' marker.
    Returns:
        A tuple (next_state, reward, done) where:
            - next_state: Updated board array
            - reward: +1 for AI win, -1 for Human win, 0 for draw
            - done: Boolean indicating game over
        """
        if not self.is_valid_move(action):
            raise ValueError(f'Invalid action {action} at step {self._step_count}')
        self._state[action] = 1 # Place AI marker (value 0)
        self._current_player = Player.PLAYER_ONE
        self._step_count += 1
        winner = self.get_winner()
        done = False
        reward = 0.0
        if winner is not None:
            done = True
            if winner == Player.AI:
                reward = 1.0
            else:
                reward = -1.0
        elif self._step_count >= self.max_steps:
            done = True
            reward = 0.0
        return (self._state.copy(), reward, done)

    def get_state_key(self, state: np.ndarray) -> Tuple[int, int]:
        """
    Encode the game board into a canonical key format.
    Args:
        state: 3x3 numpy array representing the board.
    Returns:
        A tuple (hashable_id, player_turn) where player_turn is the next move index.
        This is used for lookup in Q-tables that require hashable keys.
        """
        state_tuple = tuple((tuple(row) for row in state.reshape(3, 3)))
        return (state_tuple, self._current_player.value)

    def get_terminal_states(self) -> dict:
        """
    Accessor for terminal states (optional implementation).
    Returns a dictionary mapping state keys to reward values.
    Raises NotImplementedError as per current task constraints.
        """
        return {}

    def get_winner(self) -> Optional[Player]:
        """
    Check the current board for a winner.
    Returns:
        Player.AI if AI wins, Player.PLAYER_ONE if Human wins, None otherwise.
        """
        board = self._state.reshape(3, 3)
        # Check rows
        for row in board:
            if np.all(row == -1):
                return Player.PLAYER_ONE
            if np.all(row == 0):
                return Player.AI
        # Check columns
        for col in range(3):
            if np.all(board[:, col] == -1):
                return Player.PLAYER_ONE
            if np.all(board[:, col] == 0):
                return Player.AI
        # Check diagonals
        if np.all(np.diag(board) == -1):
            return Player.PLAYER_ONE
        if np.all(np.diag(board) == 0):
            return Player.AI
        if np.all(np.diag(np.fliplr(board)) == -1):
            return Player.PLAYER_ONE
        if np.all(np.diag(np.fliplr(board)) == 0):
            return Player.AI
        return None

    def is_game_over(self) -> bool:
        """
    Check if the game has ended.
    Returns:
        True if the game is over (winner or draw/limit), False otherwise.
        """
        return self.get_winner() is not None or self._step_count >= self.max_steps

    def is_valid_move(self, action: int) -> bool:
        """
    Check if a move is valid (cell is empty).
    Args:
        action: Index of the cell.
    Returns:
        True if the cell is empty and within bounds, False otherwise.
        """
        if not isinstance(action, int) or action < 0 or action >= 9:
            return False
        return self._state[action] == -1

    def get_current_player(self) -> Player:
        """
    Get the current player's turn.
    Returns:
        The Player enum representing the current turn.
        """
        return self._current_player

    def get_step_count(self) -> int:
        """
    Get the current number of steps taken in this episode.
    Returns:
        Integer count of steps.
        """
        return self._step_count
