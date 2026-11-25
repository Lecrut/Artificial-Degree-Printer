"""Defines the Tic-Tac-Toe game environment with state representation, move validation, and win/draw detection for reinforcement learning."""
import numpy as np
from typing import Optional
BOARD_SIZE: int = 9
EMPTY_CELL: int = 0
PLAYER_X: int = 1
PLAYER_O: int = -1

class TicTacToeEnv:
    """A class managing the Tic-Tac-Toe game state, including board initialization, move validation, and terminal condition tracking."""
    board: np.ndarray
    current_player: int
    history: list[int]
    terminal_state: bool
    winner: Optional[str]
    draw: bool

    def reset(self) -> dict:
        """Creates a new empty board and sets the first player to move. Returns state dict with board, current_player, history, winner, and draw."""
        self.board = np.zeros(BOARD_SIZE, dtype=np.int32)
        self.current_player = PLAYER_X
        self.history = []
        self.terminal_state = False
        self.winner = None
        self.draw = False
        return {'board': self.board.copy(), 'current_player': self.current_player, 'history': self.history.copy(), 'winner': self.winner, 'draw': self.draw}

    def step(self, action: int) -> tuple[np.ndarray, float, bool, bool, dict]:
        """Executes a turn by the current player. Returns observation, reward, terminated, truncated, and info dict."""
        valid_move = True
        game_over = False
        reward = 0.0
        terminated = False
        truncated = False
        if not (0 <= action < BOARD_SIZE and self.board[action] == EMPTY_CELL):
            obs = self.board.copy()
            info = {'valid_move': False, 'game_over': False}
            return (obs, reward, terminated, truncated, info)
        self.board[action] = self.current_player
        self.history.append(self.current_player)
        obs = self.board.copy()
        winner_val = self._check_win(obs)
        is_draw = self._check_draw(obs)
        if winner_val is not None:
            terminated = True
            game_over = True
            self.terminal_state = True
            reward = 1.0 if self.current_player == winner_val else -1.0
            self.winner = 'X' if winner_val == PLAYER_X else 'O'
        elif is_draw:
            terminated = True
            truncated = False
            game_over = True
            self.terminal_state = True
            self.draw = True
            self.winner = 'draw'
            reward = 0.0
        else:
            self.current_player = PLAYER_O if self.current_player == PLAYER_X else PLAYER_X
        info = {'valid_move': True, 'game_over': game_over}
        return (obs, reward, terminated, truncated, info)

    def __init__(self) -> None:
        """Initializes the Tic-Tac-Toe environment state with a new empty board and first player."""
        self.board: np.ndarray = np.zeros(BOARD_SIZE, dtype=np.int32)
        self.current_player: int = PLAYER_X
        self.history: list[int] = []
        self.terminal_state: bool = False
        self.winner: Optional[str] = None
        self.draw: bool = False

    def _check_win(self, board: np.ndarray) -> Optional[int]:
        """Checks for a winner. Returns 1 if X wins, -1 if O wins, None otherwise."""
        for i in range(0, 9, 3):
            if board[i] == board[i + 1] == board[i + 2] and board[i] != EMPTY_CELL:
                return board[i]
        for i in range(3):
            if board[i] == board[i + 3] == board[i + 6] and board[i] != EMPTY_CELL:
                return board[i]
        if board[0] == board[4] == board[8] and board[0] != EMPTY_CELL:
            return board[0]
        if board[2] == board[4] == board[6] and board[2] != EMPTY_CELL:
            return board[2]
        return None

    def _check_draw(self, board: np.ndarray) -> bool:
        """Checks if the board is full (draw)."""
        return int(EMPTY_CELL) not in board

def get_valid_moves(env: TicTacToeEnv) -> list[int]:
    """Returns a sorted list of integer indices representing all currently empty cells."""
    valid = []
    for i in range(BOARD_SIZE):
        if env.board[i] == EMPTY_CELL:
            valid.append(i)
    return valid
