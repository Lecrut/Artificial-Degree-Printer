"""Tic-Tac-Toe game environment simulation."""
import random
from typing import Tuple, Callable

class GameState:
    """Represents the board state of Tic-Tac-Toe."""
    __slots__ = ['board', 'winner', 'is_over']

    def __init__(self, board: list | None=None, winner: int | None=None, is_over: bool=False) -> None:
        """Initialize a Tic-Tac-Toe state.

    Args:
        board: The board configuration as a list of 9 integers (0=empty, 1=X, 2=O).
               If None, defaults to an empty board. Returns the state ready for simulation.
               Also accepts a dictionary mapping keys like 'a1' to values like 'X', 'O', or empty/0.
        winner: The determined winner (1=X, 2=O, -1=Draw). If None, no winner yet.
               Note: Winner is only valid if is_over=True.
        is_over: Whether the game has ended.

    Returns:
        self: An initialized GameState object ready for applying moves and checking win conditions.
    """
        if board is not None and isinstance(board, dict):
            mapping = {'a1': 0, 'a2': 1, 'a3': 2, 'b1': 3, 'b2': 4, 'b3': 5, 'c1': 6, 'c2': 7, 'c3': 8}
            temp_board = [0] * 9
            for k, v in board.items():
                if k in mapping:
                    idx = mapping[k]
                    if isinstance(v, str):
                        val = 1 if v.upper() == 'X' else 2 if v.upper() == 'O' else 0
                    else:
                        val = int(v)
                    temp_board[idx] = val
            board = temp_board
        elif board is None:
            board = [0] * 9
        self.board = board
        self.winner = winner
        self.is_over = is_over

    def copy(self) -> 'GameState':
        """Return a deep copy of the state."""
        new_state = GameState()
        new_state.board = self.board.copy()
        new_state.winner = self.winner
        new_state.is_over = self.is_over
        return new_state

    def apply_action(self, player: int, action: int) -> 'GameState':
        """Apply a move by the given player and return the new state."""
        if not 0 <= action < 9:
            raise ValueError('Action must be an integer between 0 and 8.')
        if self.board[action] != 0:
            raise ValueError('Cell is not empty.')
        new_board = self.board.copy()
        new_board[action] = player
        winner = check_winner(new_board)
        new_state = GameState(board=new_board, winner=winner)
        new_state.is_over = new_state.winner is not None
        return new_state

def check_winner(board: list | GameState) -> tuple[int, str]:
    """Determine the winner of the board state.

    Args:
        board: The current board configuration as a list of integers (0=empty, 1=X, 2=O)
               OR a GameState object. Expected format: [cell0, cell1, ..., cell8].

    Returns:
        tuple[int, str]: A tuple indicating the game state and reason:
             - (0, 'No winner') if the game is still ongoing.
             - (1, 'X wins') if Player X (1) wins.
             - (2, 'O wins') if Player O (2) wins.
             - (-1, 'Draw') if it is a Draw.
    """
    if isinstance(board, GameState):
        actual_board = board.board
    else:
        actual_board = list(board)
    if all((cell != 0 for cell in actual_board)):
        return (-1, 'Draw')
    win_combos = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]]
    for combo in win_combos:
        c0, c1, c2 = (actual_board[combo[0]], actual_board[combo[1]], actual_board[combo[2]])
        if c0 != 0 and c1 == c0 and (c2 == c0):
            return (c0, 'X wins' if c0 == 1 else 'O wins')
    return (0, 'No winner')

class GameEnvironment:
    """Manages a single game instance between two players."""

    def __init__(self) -> None:
        self.reset()

    def reset(self, board: list[int] | None=None) -> 'GameState':
        """Initialize or reset the game environment state.

    Args:
        board: Optional initial board configuration. If None, a fresh empty board is generated.

    Returns:
        GameState: The current state of the game including the board and winner information.
    """
        import numpy as np
        if board is None:
            board = [0] * 9
        self.current_board = board
        self.winner = None
        self.is_over = False
        self.turn = 1
        return GameState(board=self.current_board.copy(), winner=None, is_over=False)

    def get_available_moves(self, state: GameState) -> set[int]:
        """Return the set of valid indices for the next player's turn."""
        return {i for i in range(9) if state.board[i] == 0}

    def simulate_episode(self, opponent_func: Callable[[int], int | None]) -> Tuple[GameState, int]:
        """Run a full game simulation against an opponent function.

    Args:
        opponent_func: A callable that takes the current player's board state (as a list) and returns their move.
                     For X (player 1), this is the user/agent. For O (player 2), this is the random agent.
                     The board passed to this function corresponds to the turn *just completed* or at start, but 
                     we adjust the state index logic to match Q-Learning's expected input format.

    Returns:
        Tuple[GameState, int]: Final game state and result code (1=O wins, -1=X wins, 0=draw).
    """
        self.current_board = [0] * 9
        self.winner = None
        self.is_over = False
        self.turn = 1
        state = GameState(board=self.current_board.copy(), winner=None, is_over=False)
        while not self.is_over:
            if self.turn == 1:
                action = opponent_func(1)
                if action is None:
                    break
                next_state_index = self.apply_action(1, action)
            else:
                action = opponent_func(2)
                if action is None:
                    break
                next_state_index = self.apply_action(2, action)
            new_board = self.current_board.copy()
            if hasattr(self.current_board, 'copy'):
                pass
            self.current_board = new_board
            self.winner = self.check_winner(new_board)[0]
            self.is_over = self.winner is not None or self.turn > 2
            if self.is_over:
                break
            self.turn += 1
        return (state, self.winner)

    def apply_action(self, player: int, action: int) -> int:
        """Apply an action to the current board.

    Args:
        player: The player ID applying the action (1 for X, 2 for O).
        action: The move index (0-8).

    Returns:
        int: Index of the resulting state if using a tabular representation logic, 
             or simply updates internal board. Based on Q_Learning expectation,
             this might need to return an integer hash or index representing the new state.
    """
        if self.current_board[action] != 0:
            raise ValueError(f'Cell {action} is not empty.')
        new_board = self.current_board.copy()
        new_board[action] = player
        state_index_hash = sum((idx * 3 ** i for i, cell in enumerate(new_board)))
        return state_index_hash

class RandomOpponentAgent:
    """A baseline agent that chooses a uniformly random available move."""

    def __init__(self, board: list | None=None, opponent_func: Callable | None=None) -> None:
        """Initialize the Random Opponent Agent.

    Args:
        board: The initial board state (list of 9 ints). If None, defaults to empty board.
               Used only for immediate state setup. Does not store the board permanently;
               the agent makes moves on demand based on current state passed to `get_move`.
        opponent_func: Optional callable that receives the full GameState and returns a move.
                       Kept for interface compatibility with GameEnvironment, though unused here.

    Returns:
        self: An initialized RandomOpponentAgent object ready for simulation.

    Notes:
        This agent acts as a baseline (uniformly random). It does not store internal history;
        the environment provides the current state to `get_move`. The passed board here is only
        a starting point if needed, but the agent's behavior depends on receiving the active
        state from the game loop.
    """
        self.board = board
        self.opponent_func = opponent_func

    def reset(self) -> None:
        """Reset the internal state of the agent."""
        pass

    def get_move(self, board: list) -> int | None:
        """Return a uniformly random available move index or None if no moves.

    Args:
        board: The current board configuration as a list of integers.

    Returns:
        int | None: A valid move index or None.
    """
        empty_indices = [i for i in range(9) if board[i] == 0]
        if not empty_indices:
            return None
        return random.choice(empty_indices)
