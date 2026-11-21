"""Implementation of Tic-Tac-Toe environment with state encoding."""
import numpy as np
from typing import Tuple, Optional, List

class TicTacToeEnv:
    """Tic-Tac-Toe game environment.
    
    Grid is 3x3. Players are 1 (X) and -1 (O).
    State encoding uses a flat tuple of length 9 for Q-table indexing.
    Internal `_current_player` tracks turn order.
    """

    def __init__(self) -> None:
        """Initialize the Tic-Tac-Toe environment.

    Sets up a 3x3 grid where X and O are the players.
    Initializes internal state to track current player.
    """
        self._board: np.ndarray = np.zeros((3, 3), dtype=np.int8)
        self._current_player: int = 1

    def reset(self) -> np.ndarray:
        """Reset the game board. Returns state encoding as numpy array of zeros.
        
        Resets internal `_current_player` to 1 (X starts).
        
        Example:
        >>> env = TicTacToeEnv()
        >>> s = env.reset()
        >>> assert s.shape == (3, 3)
        >>> assert np.all(s == 0)
        """
        raise NotImplementedError

    def step(self, action: int) -> Tuple[float, bool, np.ndarray]:
        """Execute an action for the current player.
        
        Args:
            action: Index 0-8 on the board.
            
        Returns:
            reward: +1 if current player wins, -1 if opponent wins, 0 for draw/ongoing.
            done: Boolean indicating game end.
            state_encoding: New flat state tuple.
            
        Example:
        >>> env = TicTacToeEnv()
        >>> s = env.reset()
        >>> r, d, _ = env.step(4)
        >>> assert r == 0
        """
        raise NotImplementedError

    def get_valid_moves(self, state: np.ndarray) -> List[int]:
        """Return list of valid action indices (0-8) for current state.
        
        Example:
        >>> env = TicTacToeEnv()
        >>> s = env.reset()
        >>> moves = env.get_valid_moves(s)
        >>> assert len(moves) == 9
        """
        raise NotImplementedError

    def encode_state(self, board: np.ndarray) -> Tuple:
        """Convert 3x3 board array to flat tuple for Q-table key.
        
        Example:
        >>> env = TicTacToeEnv()
        >>> board = np.zeros((3, 3))
        >>> s = env.encode_state(board)
        >>> assert isinstance(s, tuple)
        """
        raise NotImplementedError

    def decode_state(self, state: Tuple) -> np.ndarray:
        """Convert flat tuple back to 3x3 board.
        
        Example:
        >>> env = TicTacToeEnv()
        >>> board = np.zeros((3, 3))
        >>> s = env.encode_state(board)
        >>> b_back = env.decode_state(s)
        >>> assert np.array_equal(board, b_back)
        """
        raise NotImplementedError
