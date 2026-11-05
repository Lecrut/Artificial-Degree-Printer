import csv
import random
from typing import Tuple, Dict
import sys
from typing import List, Literal, Optional
BoardState = List[List[Optional[str]]]
PLAYER_X: str = 'X'
PLAYER_O: str = 'O'
DRAW_STATE: str = 'D'
EMPTY_STATE: str = '.'

def check_winner(board: BoardState) -> Optional[str]:
    """
    Evaluate the Tic-Tac-Toe board to determine if there is a winner or a draw.

    Algorithmic Steps:
    1. Check all 3 rows for a winning line (XXX or OOO).
    2. Check all 3 columns for a winning line.
    3. Check both main diagonals for a winning line.
    4. If no winner is found, check if the board is full (draw condition).
    5. Return the winner ('X', 'O') or None (if game continues). Note: 
       A full board with no winner returns DRAW_STATE.

    Time Complexity: O(1) since board size is fixed (3x3).
    Space Complexity: O(1)

    Args:
        board: A 3x3 list representing the current game state.

    Returns:
        'X' if player X wins, 'O' if player O wins,
        'D' if it is a draw, or None if the game is ongoing.
    """
    for row in board:
        if row[0] == row[1] == row[2] and row[0] in (PLAYER_X, PLAYER_O):
            return row[0]
    for col_idx in range(3):
        if board[0][col_idx] == board[1][col_idx] == board[2][col_idx] and board[0][col_idx] in (PLAYER_X, PLAYER_O):
            return board[0][col_idx]
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] in (PLAYER_X, PLAYER_O):
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] in (PLAYER_X, PLAYER_O):
        return board[0][2]
    is_full: bool = all((cell is not None and cell != EMPTY_STATE for row in board for cell in row))
    if is_full:
        return DRAW_STATE
    return None

def train_and_evaluate(csv_out_path: str, episodes: int=EPISODES) -> Dict[str, float]:
    """
    Train a Q-Learning agent on Tic-Tac-Toe and evaluate its performance.

    This function simulates 'episodes' games where the agent plays against a random opponent.
    It updates the Q-table using the standard Q-learning update rule:
    Q(s, a) <- Q(s, a) + ALPHA * (R + GAMMA * max_a'(Q(s', a')) - Q(s, a))

    The results (win_rate and draw_rate) are saved to a CSV file.

    Time Complexity: O(episodes * game_length), where game_length <= 9.
    Space Complexity: O(1) relative to board state (Q-table size is fixed at 3^9). Note: 
       In practice, we use a dict for sparse storage of reachable states.

    Args:
        csv_out_path: Path to the output CSV file for saving results.
        episodes: Number of training games to simulate.

    Returns:
        A dictionary containing 'win_rate' and 'draw_rate' as floats.
    """
    q_table: Dict[Tuple[str, ...], Dict[int, float]] = {}

    def get_q(state_tuple: Tuple[str, ...], action: int) -> float:
        if state_tuple not in q_table:
            q_table[state_tuple] = {i: 0.0 for i in range(9)}
        return q_table[state_tuple][action]

    def set_q(state_tuple: Tuple[str, ...], action: int, value: float) -> None:
        if state_tuple not in q_table:
            q_table[state_tuple] = {i: 0.0 for i in range(9)}
        q_table[state_tuple][action] = value

    def get_legal_moves(board: BoardState) -> list[int]:
        """Return list of indices (0-8) for empty cells."""
        legal = []
        for r in range(3):
            for c in range(3):
                if board[r][c] == EMPTY_STATE:
                    legal.append(r * 3 + c)
        return legal

    def make_move(board: BoardState, idx: int, player: str) -> None:
        r, c = divmod(idx, 3)
        board[r][c] = player

    def undo_move(board: BoardState, idx: int) -> None:
        r, c = divmod(idx, 3)
        board[r][c] = EMPTY_STATE
    wins: int = 0
    draws: int = 0
    losses: int = 0
    random.seed(42)
    for _ in range(episodes):
        board: BoardState = [[EMPTY_STATE] * 3 for _ in range(3)]
        current_player: str = PLAYER_X
        opponent: str = PLAYER_O
        game_history: list[tuple[Tuple[str, ...], int, str]] = []
        done: bool = False
        while not done:
            state_tuple: Tuple[str, ...] = tuple((cell for row in board for cell in row))
            legal_moves: list[int] = get_legal_moves(board)
            if not legal_moves:
                break
            if random.random() < EPSILON and current_player == PLAYER_X:
                action = random.choice(legal_moves)
            else:
                max_q_val: float = -float('inf')
                best_actions: list[int] = []
                for a in legal_moves:
                    q_val = get_q(state_tuple, a)
                    if q_val > max_q_val:
                        max_q_val = q_val
                        best_actions = [a]
                    elif q_val == max_q_val:
                        best_actions.append(a)
                action = random.choice(best_actions)
            make_move(board, action, current_player)
            game_history.append((state_tuple, action, current_player))
            winner: Optional[str] = check_winner(board)
            if winner is not None:
                done = True
                if winner == PLAYER_X:
                    wins += 1
                    reward: float = 1.0
                elif winner == PLAYER_O:
                    losses += 1
                    reward: float = -1.0
                else:
                    draws += 1
                    reward: float = 0.5
                current_q_val: float = get_q(game_history[-1][0], game_history[-1][1])
                set_q(game_history[-1][0], game_history[-1][1], current_q_val + ALPHA * (reward - current_q_val))
                break
            next_player: str = opponent if current_player == PLAYER_X else PLAYER_X
            current_player = next_player
            if current_player == PLAYER_O:
                opp_legal_moves: list[int] = get_legal_moves(board)
                if not opp_legal_moves:
                    break
                opp_action: int = random.choice(opp_legal_moves)
                make_move(board, opp_action, opponent)
                winner = check_winner(board)
                if winner is not None:
                    done = True
                    if winner == PLAYER_X:
                        wins += 1
                        reward = 1.0
                    elif winner == PLAYER_O:
                        losses += 1
                        reward = -1.0
                    else:
                        draws += 1
                        reward = 0.5
                    if game_history:
                        h_state, h_act, h_player = game_history[-1]
                        current_q_val = get_q(h_state, h_act)
                        set_q(h_state, h_act, current_q_val + ALPHA * (reward - current_q_val))
                    break
                current_player = PLAYER_X
    total_games: float = float(wins + draws + losses) if wins + draws + losses > 0 else 1.0
    win_rate: float = wins / total_games
    draw_rate: float = draws / total_games
    with open(csv_out_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['method', 'win_rate', 'draw_rate'])
        writer.writerow(['q_learning_agent', f'{win_rate:.4f}', f'{draw_rate:.4f}'])
    return {'win_rate': win_rate, 'draw_rate': draw_rate}
