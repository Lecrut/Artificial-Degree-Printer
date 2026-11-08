"""
Core module for Tic-Tac-Toe Q-Learning simulation.

Provides board evaluation logic and the main training/evaluation loop
using tabular Q-Learning with epsilon-greedy policy.
"""
from __future__ import annotations
import random
import csv
from typing import TYPE_CHECKING, Callable, Dict, List, Tuple
if TYPE_CHECKING:
    from config import ALPHA, GAMMA, EPSILON, EPISODES
from config import ALPHA, GAMMA, EPSILON, EPISODES

def check_winner(board: list[int]) -> str:
    """Evaluate the Tic-Tac-Toe board state.

    Determines if there is a winner ('X' for player 1, 'O' for player -1) or if it's a draw/ongoing ('DRAW').

    Args:
        board: A flat list of 9 integers representing the board state.
               1 indicates player X, -1 indicates player O, and 0 indicates an empty cell.

    Returns:
        'X' if Player X wins, 'O' if Player O wins, 'DRAW' otherwise (draw or ongoing).

    Raises:
        ValueError: If the board length is not exactly 9.

    Complexity:
        Time: O(1) as it checks a fixed number of winning lines (8 total).
        Space: O(1)
    """
    if len(board) != 9:
        raise ValueError('Board must have exactly 9 cells.')
    lines = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]]
    for line in lines:
        s = board[line[0]] + board[line[1]] + board[line[2]]
        if s == 3:
            return 'X'
        if s == -3:
            return 'O'
    if all((cell != 0 for cell in board)):
        return 'DRAW'
    return 'DRAW'

def train_and_evaluate(csv_out_path: str) -> dict[str, float]:
    """Train a Q-Learning agent on Tic-Tac-Toe and evaluate performance.

    Simulates EPISODES episodes of self-play. The agent uses an epsilon-greedy policy
    for action selection. After training, it evaluates the agent against a random opponent
    to calculate win and draw rates.

    Args:
        csv_out_path: Path to save the results CSV file.

    Returns:
        A dictionary containing 'win_rate' and 'draw_rate' as floats.
    """
    from config import ALPHA, GAMMA, EPSILON, EPISODES
    random.seed(42)

    def get_state_key(board: list[int]) -> tuple[int, ...]:
        return tuple(board)
    q_table: dict[tuple[int, ...], list[float]] = {}

    def get_q_values(state: tuple[int, ...]) -> list[float]:
        if state not in q_table:
            q_table[state] = [0.0] * 9
        return q_table[state]

    def choose_action(board: list[int], is_training: bool=True) -> int:
        """Choose a move using epsilon-greedy policy.

        Args:
            board: Current board state.
            is_training: If True, applies epsilon exploration. Else, greedy exploitation.

        Returns:
            Index of the chosen legal move. -1 if no moves are left (should not happen in valid game flow).
        """
        legal_moves = [i for i, cell in enumerate(board) if cell == 0]
        if not legal_moves:
            return -1
        if is_training and random.random() < EPSILON:
            return random.choice(legal_moves)
        state = get_state_key(board)
        q_vals = get_q_values(state)
        max_q = -float('inf')
        for i in legal_moves:
            if q_vals[i] > max_q:
                max_q = q_vals[i]
        best_moves = [i for i in legal_moves if q_vals[i] == max_q]
        return random.choice(best_moves)

    def make_move(board: list[int], player: int, move_idx: int) -> list[int]:
        """Apply a move to the board and return new state.

        Args:
            board: Current board state.
            player: Player ID (1 or -1).
            move_idx: Index on the board to place the move.

        Returns:
            New board state with the move applied.
        """
        new_board = board.copy()
        new_board[move_idx] = player
        return new_board
    for _ in range(EPISODES):
        board: list[int] = [0] * 9
        turn: int = 1
        while True:
            state = get_state_key(board)
            action = choose_action(board, is_training=True)
            if action == -1:
                break
            next_board = make_move(board, turn, action)
            winner_str = check_winner(next_board)
            winner_num: int = 0
            if winner_str == 'X':
                winner_num = 1
            elif winner_str == 'O':
                winner_num = -1
            current_q_vals = get_q_values(state)
            current_q = current_q_vals[action]
            if winner_num != 0:
                reward: float = 1.0 if winner_num == turn else -1.0
                new_q = current_q + ALPHA * (reward - current_q)
                q_table[state][action] = new_q
                break
            else:
                next_state = get_state_key(next_board)
                next_q_vals = get_q_values(next_state)
                max_next_q = max(next_q_vals)
                reward = 0.0
                new_q = current_q + ALPHA * (reward + GAMMA * max_next_q - current_q)
                q_table[state][action] = new_q
            board = next_board
            turn = -turn
    num_eval_games: int = 1000
    wins: int = 0
    draws: int = 0
    losses: int = 0
    for _ in range(num_eval_games):
        eval_board: list[int] = [0] * 9
        eval_turn: int = 1
        while True:
            agent_move = choose_action(eval_board, is_training=False)
            if agent_move == -1:
                draws += 1
                break
            eval_board = make_move(eval_board, eval_turn, agent_move)
            winner_str = check_winner(eval_board)
            if winner_str != 'DRAW':
                if winner_str == 'X':
                    wins += 1
                else:
                    losses += 1
                break
            eval_turn = -eval_turn
            if eval_turn == -1:
                legal_moves = [i for i, cell in enumerate(eval_board) if cell == 0]
                if not legal_moves:
                    draws += 1
                    break
                opp_move = random.choice(legal_moves)
                eval_board = make_move(eval_board, -1, opp_move)
                winner_str = check_winner(eval_board)
                if winner_str != 'DRAW':
                    if winner_str == 'X':
                        wins += 1
                    else:
                        losses += 1
                    break
                eval_turn = 1
            else:
                draws += 1
                break
    win_rate: float = wins / num_eval_games
    draw_rate: float = draws / num_eval_games
    loss_rate: float = losses / num_eval_games
    with open(csv_out_path, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['method', 'rounds', 'win_rate', 'draw_rate', 'loss_rate'])
        writer.writerow(['proposed_qlearn', EPISODES, win_rate, draw_rate, loss_rate])
    return {'win_rate': float(win_rate), 'draw_rate': float(draw_rate)}
