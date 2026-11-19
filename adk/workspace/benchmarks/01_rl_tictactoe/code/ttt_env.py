"""Tic-Tac-Toe board environment implementing state management and game rules."""
import random
from typing import List, Tuple

class Board:
    """Represents the Tic-Tac-Toe game board and state transitions."""
    board: 'object'

    def __init__(self) -> None:
        """Initializes an empty 3x3 board for a new game.

    Sets up the internal representation of the board as a list of length 9.

    Attributes:
        board: A list of integers representing the 3x3 board.
    """
        self.board = [0] * 9

    def reset(self) -> 'Board':
        """Resets the board to an empty state.

Replaces the current board configuration with a fresh empty one and returns self.

Returns:
    Board: The current board instance (self).
"""
        self.board = [0] * 9
        return self

    def get_state_hash(self) -> str:
        """Returns a canonical string representation of the current board state.

    Converts the internal list into a 9-character string where '1' is X, '-1' is O, and '0' is empty.

    Returns:
        str: A 9-character string representing the board state.
    """
        return ''.join((str(x) for x in self.board))

    def get_legal_moves(self) -> List[int]:
        """Returns a list of indices corresponding to empty squares.

    Identifies all positions on the board that do not yet have a value.

    Returns:
        List[int]: A list of integers (0-8) representing valid move positions.
    """
        return [i for i, val in enumerate(self.board) if val == 0]

    def is_terminal(self) -> bool:
        """Checks if the game has ended due to a win or draw.

Evaluates all possible lines on the board for completed sequences.

Returns:
bool: True if the game is over (win or draw), False otherwise.
"""
        lines = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]]
        for line in lines:
            if self.board[line[0]] == self.board[line[1]] == self.board[line[2]] != 0:
                return True
        if not any((val == 0 for val in self.board)):
            return True
        return False

    def get_winner(self) -> int:
        """Returns the winner of the game. 1 for Player X, -1 for Player O, 0 for draw.

Determines the outcome based on the current board configuration.

Returns:
    int: 1 if X wins, -1 if O wins, 0 if draw.
"""
        if self.is_terminal():
            lines = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]]
            for line in lines:
                v1, v2, v3 = (self.board[line[0]], self.board[line[1]], self.board[line[2]])
                if v1 == v2 == v3 and v1 != 0:
                    return v1
            return 0
        return 0

    def step(self, action: int) -> Tuple[float, bool]:
        """Executes a move for the current active player and returns the result.

    Updates the board state based on the given action index. The caller must track
    whose turn it is to determine if they are the actor or opponent for reward calculation.

    Args:
        action (int): The index of the square to play (0-8).

    Returns:
        Tuple[float, bool]: A tuple containing the reward (-1 loss, 0 draw, 1 win)
                            relative to the **actor** who just moved, and whether the game is terminal.
                            Note: This function only updates state. The caller (agent) must decide
                            whether to use this reward for Q-learning updates based on whether
                            the agent itself performed the move.
    """
        if action not in self.get_legal_moves():
            raise ValueError(f'Invalid action {action}. Legal moves: {self.get_legal_moves()}')
        self.board[action] = 1
        reward = -1 if self.get_winner() == -1 else 0 if self.get_winner() == 0 else 1
        terminal = self.is_terminal()
        return (float(reward), terminal)

def get_random_move(board: Board) -> int:
    """Selects a random legal move from the board.

    Picks a random index from the list of available moves provided by the board.

    Args:
        board (Board): The current game board state.

    Returns:
        int: A randomly chosen valid move index.
    """
    legal_moves = board.get_legal_moves()
    if not legal_moves:
        raise ValueError('No legal moves available. Game is full.')
    return random.choice(legal_moves)
