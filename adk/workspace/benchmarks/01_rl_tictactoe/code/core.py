"""Core logic for Tic-Tac-Toe Q-Learning Agent.

Provides board evaluation, state representation, and a Tabular Q-Learning agent
for training against a random opponent.
"""
from __future__ import annotations
import csv
import random
from dataclasses import dataclass, field
from typing import Any
from config import ALPHA as LEARNING_RATE
from config import EPISODES as NUM_EPISODES
from config import GAMMA as DISCOUNT_FACTOR
from config import EPSILON as EXPLORATION_RATE

def check_winner(board: list[int]) -> int:
    """Evaluate the Tic-Tac-Toe board state.

    Determines if there is a winner or if the game is a draw.

    Args:
        board: A flat list of length 9 representing the board cells.
            0 = empty, 1 = X (agent), -1 = O (opponent).

    Returns:
        1 if player 'X' wins,
        -1 if player 'O' wins,
        0 if the game is a draw or ongoing.
    """
    winning_lines: tuple[tuple[int, ...], ...] = ((0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6))
    for a, b, c in winning_lines:
        if board[a] != 0 and board[a] == board[b] == board[c]:
            return board[a]
    return 0

def _q_table_state_key(board: list[int]) -> tuple[int, ...]:
    """Convert a board state list to a hashable tuple key for the Q-table.

    Args:
        board: Current board state as a list of integers.

    Returns:
        A tuple representing the board state.
    """
    return tuple(board)

def _get_legal_moves(board: list[int]) -> list[int]:
    """Retrieve indices of empty cells (legal moves).

    Args:
        board: Current board state.

    Returns:
        List of integer indices corresponding to empty cells.
    """
    return [i for i, cell in enumerate(board) if cell == 0]

@dataclass(frozen=True)
class QLearningAgent:
    """A Tabular Q-Learning agent for Tic-Tac-Toe.

    Attributes:
        q_table: Dictionary mapping states (tuples) to action values.
        alpha: Learning rate.
        gamma: Discount factor.
        epsilon: Exploration rate.
    """
    q_table: dict[tuple[int, ...], dict[int, float]] = field(default_factory=dict)
    alpha: float = LEARNING_RATE
    gamma: float = DISCOUNT_FACTOR
    epsilon: float = EXPLORATION_RATE

    def choose_action(self, state_key: tuple[int, ...], legal_moves: list[int]) -> int:
        """Select an action using the epsilon-greedy policy.

        Args:
            state_key: The current board state as a tuple.
            legal_moves: List of available move indices.

        Returns:
            The chosen action index.
        """
        if random.random() < self.epsilon:
            return random.choice(legal_moves)
        if state_key not in self.q_table:
            self.q_table[state_key] = {i: 0.0 for i in range(9)}
        q_vals = self.q_table[state_key]
        best_val = max((q_vals[m] for m in legal_moves))
        best_actions = [m for m in legal_moves if q_vals[m] == best_val]
        return random.choice(best_actions)

    def update(self, state_key: tuple[int, ...], action: int, reward: float, next_state_key: tuple[int, ...]) -> None:
        """Update the Q-value for a state-action pair.

        Args:
            state_key: The previous board state.
            action: The action taken.
            reward: The immediate reward received.
            next_state_key: The resulting board state after the action.
        """
        if state_key not in self.q_table:
            self.q_table[state_key] = {i: 0.0 for i in range(9)}
        current_q = self.q_table[state_key][action]
        if next_state_key not in self.q_table:
            self.q_table[next_state_key] = {i: 0.0 for i in range(9)}
        max_next_q = max(self.q_table[next_state_key].values())
        self.q_table[state_key][action] = current_q + self.alpha * (reward + self.gamma * max_next_q - current_q)

    def get_legal_moves(self, board: list[int]) -> list[int]:
        """Alias for _get_legal_moves to support polymorphic agent interfaces if needed.

        Args:
            board: Current board state.

        Returns:
            List of available move indices.
        """
        return _get_legal_moves(board)

    def get_q_values(self, state_key: tuple[int, ...]) -> dict[int, float]:
        """Retrieve Q-values for a given state.

        Args:
            state_key: The board state tuple.

        Returns:
            Dictionary mapping moves to Q-values. Initializes if not present.
        """
        if state_key not in self.q_table:
            self.q_table[state_key] = {i: 0.0 for i in range(9)}
        return self.q_table[state_key]

def train_and_evaluate(csv_out_path: str = 'results.csv', n_runs: int = 50, seed: int = 42) -> dict[str, float]:
    """Train Q-Learning agent against a random opponent and evaluate performance.

    Runs the training process `n_runs` times to average out stochasticity,
    then saves aggregated metrics to a CSV file matching standard schema.

    Args:
        csv_out_path: Path to the output CSV file for benchmarking results.
        n_runs: Number of independent training runs to average over (default 50).
        seed: Random seed for reproducibility (default 42).

    Returns:
        Dictionary containing averaged 'win_rate', 'draw_rate', and 'loss_rate'.
    """
    from config import ALPHA as LEARNING_RATE
    from config import GAMMA as DISCOUNT_FACTOR
    from config import EPSILON as EXPLORATION_RATE
    
    cumulative_win_rates: list[float] = []
    cumulative_draw_rates: list[float] = []
    cumulative_loss_rates: list[float] = []
    
    for run in range(n_runs):
        agent = QLearningAgent()
        random.seed(seed + run)
        win_count: int = 0
        draw_count: int = 0
        loss_count: int = 0
        
        for _ in range(NUM_EPISODES):
            board: list[int] = [0] * 9
            turn: int = 1
            final_reward: float = 0.0
            terminated: bool = False
            
            while not terminated:
                state_key: tuple[int, ...] = _q_table_state_key(board)
                legal_moves: list[int] = _get_legal_moves(board)
                
                if not legal_moves:
                    final_reward = 0.0
                    terminated = True
                    break
                
                if turn == 1:
                    action = agent.choose_action(state_key, legal_moves)
                    board[action] = 1
                    winner = check_winner(board)
                    if winner != 0:
                        final_reward = float(winner)
                        terminated = True
                        break
                    else:
                        next_state_key = _q_table_state_key(board)
                        agent.update(state_key, action, 0.0, next_state_key)
                        turn = -1
                else:
                    action = random.choice(legal_moves)
                    board[action] = -1
                    winner = check_winner(board)
                    if winner != 0:
                        final_reward = float(winner)
                        terminated = True
                        break
                    else:
                        turn = 1
            
            if final_reward == 1.0:
                win_count += 1
            elif final_reward == -1.0:
                loss_count += 1
            else:
                draw_count += 1
        
        cumulative_win_rates.append(win_count / NUM_EPISODES)
        cumulative_draw_rates.append(draw_count / NUM_EPISODES)
        cumulative_loss_rates.append(loss_count / NUM_EPISODES)
        
    n: int = len(cumulative_win_rates)
    mean_win: float = sum(cumulative_win_rates) / n if n > 0 else 0.0
    std_dev_win: float = (sum(((x - mean_win) ** 2 for x in cumulative_win_rates)) / max(n - 1, 1)) ** 0.5 if n > 1 else 0.0
    
    mean_draw: float = sum(cumulative_draw_rates) / n if n > 0 else 0.0
    std_dev_draw: float = (sum(((x - mean_draw) ** 2 for x in cumulative_draw_rates)) / max(n - 1, 1)) ** 0.5 if n > 1 else 0.0
    
    mean_loss: float = sum(cumulative_loss_rates) / n if n > 0 else 0.0
    std_dev_loss: float = (sum(((x - mean_loss) ** 2 for x in cumulative_loss_rates)) / max(n - 1, 1)) ** 0.5 if n > 1 else 0.0
    
    avg_metrics: dict[str, float] = {'win_rate': mean_win, 'draw_rate': mean_draw, 'loss_rate': mean_loss}
    
    with open(csv_out_path, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['metric', 'mean', 'std_dev'])
        writer.writeheader()
        writer.writerow({'metric': 'win_rate', 'mean': mean_win, 'std_dev': std_dev_win})
        writer.writerow({'metric': 'draw_rate', 'mean': mean_draw, 'std_dev': std_dev_draw})
        writer.writerow({'metric': 'loss_rate', 'mean': mean_loss, 'std_dev': std_dev_loss})
    
    return avg_metrics
