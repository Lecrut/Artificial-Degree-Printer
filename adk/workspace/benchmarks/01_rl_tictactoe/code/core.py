"""
Core logic for Tic-Tac-Toe Q-Learning Agent.

This module implements the game state representation, board evaluation,
a tabular Q-learning agent for adversarial search, and a deterministic
evaluation pipeline that exports metrics to CSV.
"""
from __future__ import annotations
import csv
import random
from typing import Final
from config import ALPHA, GAMMA, EPSILON, EPISODES

BOARD_SIZE: Final[int] = 3
EMPTY_SYMBOL: Final[str] = ' '
PLAYER_X: Final[str] = 'X'
PLAYER_O: Final[str] = 'O'
WIN_LENGTH: Final[int] = 3


def check_winner(board: list[list[str]] | list[str]) -> str | None:
    """Evaluate the board state to determine the game outcome.

    Checks all rows, columns, and diagonals for a winner. Returns
    the winning player's symbol ('X' or 'O'), or None if no winner
    exists yet. If the board is full and no winner exists, it returns
    'D' (Draw). Handles both 2D (list[list[str]]) and 1D (list[str])
    representations by normalizing to a flattened view for logic.

    Args:
        board: A 3x3 list of lists OR a flat list of 9 strings representing
            the board state. Rows represent horizontal lines if 2D,
            columns vertical. If 1D, indices correspond to standard
            row-major flattening (0-8).

    Returns:
        The winning symbol ('X', 'O'), 'D' for draw, or None for ongoing.

    Raises:
        ValueError: If board dimensions are not exactly 3x3 (or length 9).

    Complexity:
        Time: O(1) - Fixed board size implies constant number of checks.
        Space: O(1)
    """
    # Normalize to 1D representation for easier indexing
    flat_board: list[str]
    if len(board) == BOARD_SIZE:
        if any(len(row) != BOARD_SIZE for row in board):
            raise ValueError(f'Board rows must have length {BOARD_SIZE}')
        flat_board = [cell for row in board for cell in row]
    elif len(board) == BOARD_SIZE ** 2:
        flat_board = list(board)
    else:
        raise ValueError(f'Board must have {BOARD_SIZE**2} cells, got {len(board)}')

    # Check rows (indices: 0,1,2; 3,4,5; 6,7,8)
    for i in range(0, 9, 3):
        if flat_board[i] == flat_board[i+1] == flat_board[i+2] != EMPTY_SYMBOL:
            return flat_board[i]

    # Check columns (indices: 0,3,6; 1,4,7; 2,5,8)
    for i in range(3):
        if flat_board[i] == flat_board[i+3] == flat_board[i+6] != EMPTY_SYMBOL:
            return flat_board[i]

    # Check diagonals (0,4,8 and 2,4,6)
    if flat_board[0] == flat_board[4] == flat_board[8] != EMPTY_SYMBOL:
        return flat_board[0]
    if flat_board[2] == flat_board[4] == flat_board[6] != EMPTY_SYMBOL:
        return flat_board[2]

    # Check for draw (if no empty spaces)
    if EMPTY_SYMBOL not in flat_board:
        return 'D'

    # Game ongoing - return None explicitly
    return None


class QLearningAgent:
    """Tabular Q-Learning Agent for Tic-Tac-Toe.

    Uses an epsilon-greedy policy to explore the state space and
    updates Q-values via the temporal difference learning rule:
    Q(s, a) <- Q(s, a) + alpha * (r + gamma * max(Q(s', a')) - Q(s, a))
    """

    def __init__(self, alpha: float = ALPHA, gamma: float = GAMMA, epsilon: float = EPSILON, seed: int = 42) -> None:
        """
        Args:
            alpha: Learning rate (default: from config).
            gamma: Discount factor (default: from config).
            epsilon: Exploration rate (default: from config).
            seed: Random seed for reproducibility.
        """
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.rng = random.Random(seed)
        self.q_table: dict[tuple[str, ...], list[float]] = {}

    def get_q_values(self, state: tuple[str, ...]) -> list[float]:
        """Retrieve or initialize Q-values for a given state.

        Args:
            state: A flattened 1D tuple representing the board state.

        Returns:
            A list of 9 floats corresponding to Q-values for each cell.
        """
        if state not in self.q_table:
            self.q_table[state] = [0.0] * BOARD_SIZE ** 2
        return self.q_table[state]

    def choose_action(self, state: tuple[str, ...], available_moves: list[int]) -> int | None:
        """
        Select an action using epsilon-greedy policy.

        Args:
            state: Current flattened board state.
            available_moves: List of indices (0-8) where moves are valid.

        Returns:
            An index from available_moves, or None if no moves remain.
        """
        if not available_moves:
            return None
        if self.rng.random() < self.epsilon:
            return self.rng.choice(available_moves)
        else:
            q_values = self.get_q_values(state)
            max_q = max((q_values[m] for m in available_moves))
            best_actions = [m for m in available_moves if abs(q_values[m] - max_q) < 1e-09]
            return self.rng.choice(best_actions)

    def update(self, state: tuple[str, ...], action: int, reward: float, next_state: tuple[str, ...]) -> None:
        """
        Update Q-value for state-action pair using TD error.

        Args:
            state: The state before the action.
            action: The index of the chosen action.
            reward: Immediate reward received (1 for win, -1 for loss, 0 otherwise).
            next_state: The state after the action.
        """
        q_values = self.get_q_values(state)
        next_q_values = self.get_q_values(next_state)
        max_next_q = max(next_q_values) if next_q_values else 0.0
        td_target = reward + self.gamma * max_next_q
        q_values[action] += self.alpha * (td_target - q_values[action])

    def train_against_random(self, episodes: int = EPISODES, seed: int = 42) -> dict[str, float]:
        """
        Train the agent by playing against a random move opponent.

        Args:
            episodes: Number of training games (default: from config).
            seed: Random seed for reproducibility.

        Returns:
            Dictionary containing 'win_rate' and 'draw_rate' metrics.
        """
        train_rng = random.Random(seed)
        wins = 0
        draws = 0
        losses = 0
        for _ in range(episodes):
            board: list[list[str]] = [[EMPTY_SYMBOL] * BOARD_SIZE for _ in range(BOARD_SIZE)]
            current_player: str = PLAYER_X
            game_over = False
            while not game_over:
                state = tuple(cell for row in board for cell in row)
                available_moves = [i for i, cell in enumerate(state) if cell == EMPTY_SYMBOL]
                if not available_moves:
                    game_over = True
                    break

                if current_player == PLAYER_X:
                    action = self.choose_action(state, available_moves)
                else:
                    action = train_rng.choice(available_moves)

                row_idx, col_idx = divmod(action, BOARD_SIZE)
                board[row_idx][col_idx] = current_player
                winner = check_winner(board)

                if winner is not None:
                    game_over = True
                    if winner == PLAYER_X:
                        wins += 1
                        reward = 1.0
                    elif winner == PLAYER_O:
                        losses += 1
                        reward = -1.0
                    else:
                        draws += 1
                        reward = 0.0

                    # Update Q-value for the player who just moved (usually X in this setup)
                    if current_player == PLAYER_X:
                        self.update(state, action, reward, state)
                    break

                # Switch player
                current_player = PLAYER_O if current_player == PLAYER_X else PLAYER_X

        total_games = wins + draws + losses
        win_rate = wins / total_games if total_games > 0 else 0.0
        draw_rate = draws / total_games if total_games > 0 else 0.0
        return {'win_rate': win_rate, 'draw_rate': draw_rate}


def train_and_evaluate(csv_out_path: str = 'results.csv', seed: int = 42) -> dict[str, float]:
    """Execute deterministic training and evaluation of the Q-Learning agent.

    Trains the agent against a random opponent for EPISODES steps,
    then evaluates performance. Saves results to a CSV file.

    Args:
        csv_out_path: Destination path for empirical benchmark metrics.
            Default is 'results.csv'.
        seed: Deterministic RNG seed (default: 42).

    Returns:
        Dictionary containing 'win_rate' and 'draw_rate' as floats.
    """
    agent = QLearningAgent(alpha=ALPHA, gamma=GAMMA, epsilon=EPSILON, seed=seed)
    metrics = agent.train_against_random(episodes=EPISODES, seed=seed)
    with open(csv_out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['metric_name', 'value'])
        writer.writeheader()
        for metric_name, value in metrics.items():
            writer.writerow({'metric_name': metric_name, 'value': value})
    return metrics