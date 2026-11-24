"""Implements the Tic-Tac-Toe game logic and a Gymnasium-compatible environment wrapper for agent interaction."""
import gymnasium as gym
from gymnasium import spaces
import numpy as np

class TicTacToeEnv(gym.Env):
    """A standard 3x3 Tic-Tac-Toe environment using Gymnasium API.

    The state is represented by a 9-element integer array where:
    - 0 represents an empty cell,
    1 represents 'X' (the first player),
    2 represents 'O' (the second player).

    Actions are integers from 0 to 8, corresponding to the indices in the flattened 3x3 board.
    """
    observation_space: 'object'
    action_space: 'object'
    board: 'np.ndarray[np.int32]'
    current_player: 'int'
    metadata = {'render_modes': ['human', 'rgb_array']}

    def __init__(self) -> None:
        """Initialize the Tic-Tac-Toe environment.

    The parent class is initialized without passing a seed, as seed handling
    is done explicitly in reset() to comply with Gymnasium conventions for
    environments that do not support seeding via __init__.
    """
        super().__init__()
        self.observation_space: spaces.Discrete = spaces.Discrete(9)
        self.action_space: spaces.Discrete = spaces.Discrete(9)
        self.metadata = {'render_modes': ['human', 'rgb_array']}
        self.board: np.ndarray[np.int32] = np.zeros(9, dtype=np.int32)
        self.current_player: int = 1

    def reset(self, *, seed: int | None=None, options: dict[str, object] | None=None) -> tuple[np.ndarray, dict]:
        """Resets the environment to an initial state.

    Returns:
        A tuple containing:
        - observation (np.ndarray): The empty board representation [0, 0, ..., 0].
        - info (dict): An info dictionary with metadata, including whose turn it is.
    """
        if seed is not None:
            np.random.seed(seed)
        self.board = np.zeros(9, dtype=np.int32)
        self.current_player = 1
        observation: np.ndarray = self.board.copy()
        info: dict = {'current_player': self.current_player}
        return (observation, info)

    def step(self, action: int) -> tuple[np.ndarray, float, bool, bool, dict]:
        """Performs a single step in the environment.

    Args:
        action (int): An integer representing the cell index to play (0-8).

    Returns:
        A tuple containing:
        - observation (np.ndarray): The board after the move.
        - reward (float): +1.0 if the acting player wins, 0.0 for a draw, -1.0 if the acting player loses.
        - terminated (bool): True if the game has ended (win/draw), False otherwise.
        - truncated (bool): Always False unless step limit is enforced.
        - info (dict): Contains 'winner' or status details.
    """
        action = int(action)
        if not 0 <= action < 9:
            raise ValueError(f'Action {action} is out of bounds for Tic-Tac-Toe (must be 0-8).')
        prev_board: np.ndarray = self.board.copy()
        player_symbol: int = self.current_player
        opponent_symbol: int = 3 - player_symbol
        if self.board[action] != 0:
            return (prev_board.copy(), 0.0, False, False, {'error': 'invalid action', 'occupied': True})
        self.board[action] = player_symbol
        reward: float = 0.0
        terminated: bool = False
        truncated: bool = False
        winner: int | None = None
        if not np.any(self.board == 0):
            reward = 0.0
            winner = 0
            terminated = True
        else:

            def check_won(board: np.ndarray, player: int) -> bool:
                return board[0] == player and board[1] == player and (board[2] == player) or (board[3] == player and board[4] == player and (board[5] == player)) or (board[6] == player and board[7] == player and (board[8] == player)) or (board[0] == player and board[3] == player and (board[6] == player)) or (board[1] == player and board[4] == player and (board[7] == player)) or (board[2] == player and board[5] == player and (board[8] == player)) or (board[0] == player and board[4] == player and (board[8] == player)) or (board[2] == player and board[4] == player and (board[6] == player))
            player_won = check_won(self.board, player_symbol)
            opponent_won = check_won(self.board, opponent_symbol)
            if player_won:
                reward = 1.0
                winner = player_symbol
                terminated = True
            elif opponent_won:
                reward = -1.0
                winner = opponent_symbol
                terminated = True
        self.current_player = 3 - self.current_player
        info: dict = {'winner': winner}
        return (self.board.copy(), reward, terminated, truncated, info)

    def __enter__(self) -> 'TicTacToeEnv':
        """Enter the context manager.

    Returns:
        self
    """
        return self

    def __exit__(self, exc_type: type | None, exc_val: object | None, exc_tb: object | None) -> bool:
        """Exit the context manager.

    Args:
        exc_type: The exception type if an exception occurred.
        exc_val: The exception value if an exception occurred.
        exc_tb: The traceback object if an exception occurred.

    Returns:
        False (no exception suppression)
    """
        return False
