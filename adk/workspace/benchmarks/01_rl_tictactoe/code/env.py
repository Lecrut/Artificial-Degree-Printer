"""Implementacja gry Kółko i Krzyżyk jako środowiska MDP."""
from typing import List, Tuple, Optional
import copy

class TicTacToeEnv:
    """Środowisko gry Kółko i Krzyżyk. Stan to lista 9 elementów [0:puste, 1:X, 2:O]."""
    board: 'object'
    current_player: 'object'
    done: 'object'
    winner: 'Optional[int]'

    def __init__(self) -> None:
        """Inicjalizuje pustą planszę."""
        self.board: List[int] = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.current_player: int = 1
        self.done: bool = False
        self.winner: Optional[int] = None

    def reset(self) -> List[int]:
        """Resets the board to initial empty state and returns it.

>>> env = TicTacToeEnv()
>>> s = env.reset()
>>> s
[0, 0, 0, 0, 0, 0, 0, 0, 0]
    """
        self.board: List[int] = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.current_player: int = 1
        self.done: bool = False
        self.winner: Optional[int] = None
        return self.board.copy()

    def get_valid_moves(self) -> List[int]:
        """Returns a list of indices (0-8) for empty cells.

    >>> env = TicTacToeEnv()
    >>> env.board[4] = 1
    >>> env.get_valid_moves() == [0,1,2,3,5,6,7,8]
    True
    """
        return [i for i in range(9) if self.board[i] == 0]

    def step(self, action: int) -> Tuple[List[int], float, bool]:
        """Executes an action. Returns (new_state, reward, done).

>>> env = TicTacToeEnv()
>>> env.reset()
[0, 0, 0, 0, 0, 0, 0, 0, 0]
>>> new_s, r, d = env.step(4)
>>> new_s[4] == 1
True
    """
        if action not in self.get_valid_moves():
            return (self.board.copy(), -0.1, False)
        self.board[action] = self.current_player
        winner_id: Optional[int] = self._check_win()
        reward: float = 0.0
        done: bool = False
        if winner_id is not None:
            done = True
            if winner_id == self.current_player:
                reward = 1.0
            else:
                reward = -1.0
        elif len([c for c in self.board if c != 0]) == 9:
            done = True
            reward = 0.0
        self.winner: Optional[int] = winner_id if winner_id is not None else None
        self.done: bool = done
        self.current_player: int = 2 if self.current_player == 1 else 1
        return (self.board.copy(), reward, done)

    def _check_win(self) -> Optional[int]:
        """Checks for win condition. Returns 1 (X wins), 2 (O wins), or None."""
        lines = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]]
        for line in lines:
            if all((self.board[i] == self.board[line[0]] and self.board[i] != 0 for i in line)):
                return self.board[line[0]]
        if all((cell != 0 for cell in self.board)):
            return None
        return None
