"""Module providing Tic-Tac-Toe board logic, state encoding, and simulation capabilities."""
from typing import Optional
import random

class Board:
    """Represents a standard 3x3 Tic-Tac-Toe board."""

    def __init__(self) -> None:
        """Initialize an empty 3x3 board."""
        self.board: list[str] = ['_'] * 9

    def reset(self) -> None:
        """Reset the board to an empty state."""
        self.board = ['_'] * 9

    def make_move(self, position: int, player: int) -> bool:
        """Place a mark on the board. Returns True if successful (valid), False otherwise."""
        if not 0 <= position <= 8:
            return False
        if self.board[position] != '_':
            return False
        self.board[position] = 'X' if player == 1 else 'O'
        return True

    def get_legal_moves(self) -> list[int]:
        """Return a list of indices for empty cells."""
        return [i for i, cell in enumerate(self.board) if cell == '_']

    def check_win(self, player: int) -> bool:
        """Check if the specified player has won.

    Returns True if the given player has three marks in a row (horizontal, vertical, or diagonal).
    """
        mark = 'X' if player == 1 else 'O' if player == -1 else None
        if mark is None:
            return False
        win_combos = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]]
        for combo in win_combos:
            if self.board[combo[0]] == mark and self.board[combo[1]] == mark and (self.board[combo[2]] == mark):
                return True
        return False

    def is_draw(self) -> bool:
        """Check if the game ended in a draw."""
        return all((cell != '_' for cell in self.board))

    def get_state_key(self) -> str:
        """Return a string representation of the current board state (e.g., 'OOX..X...')."""
        return ''.join(self.board)

def simulate_game(config: dict) -> tuple[int, int]:
    """Run a single game between an Agent and a Random Opponent. Returns (agent_reward, opponent_reward)."""
    agent = 0
    random_opp = 1
    board = Board()
    while True:
        if board.check_win(agent):
            return (1, -1)
        elif board.is_draw():
            return (0.5, 0.5)
        opponent_reward = 0
        agent_reward = 0
        moves = board.get_legal_moves()
        if not moves:
            break
        next_move = ''
        if config.get('use_agent', False):
            state_key = board.get_state_key()
            if len(moves) == 1:
                next_move = moves[0]
            else:
                next_move = random.choice(moves)
        else:
            next_move = random.choice(moves)
        board.make_move(next_move, agent if config.get('use_agent', False) else random_opp)
    if board.check_win(agent):
        return (1, -1)
    elif board.check_win(random_opp):
        return (-1, 1)
    else:
        return (0.5, 0.5)

def check_win(self, player: int) -> bool:
    """Check if the specified player has won."""
    mark = 'X' if player == 1 else 'O'
    win_combos = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]]
    for combo in win_combos:
        if self.board[combo[0]] == mark and self.board[combo[1]] == mark and (self.board[combo[2]] == mark):
            return True
    return False
