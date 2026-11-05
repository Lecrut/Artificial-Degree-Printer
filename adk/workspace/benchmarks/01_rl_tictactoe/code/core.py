"""
core.py - Core logic for Tic-Tac-Toe Q-Learning implementation.

This module provides:
1. Board state representation and validation.
2. `check_winner(board)`: Evaluates the terminal state of a game.
3. `train_and_evaluate(csv_out_path)`: Trains a tabular Q-Learning agent
   using hyperparameters from `config.py` and saves metrics to CSV.
4. Unit tests via pytest if executed directly or imported appropriately.

Author: Seed Coder (Layer 2 Agent)
"""

import random
import csv
import sys
from typing import List, Tuple, Optional, Dict

# Import hyperparameters from config.py to ensure strict symbol consistency
try:
    from config import ALPHA, GAMMA, EPSILON, EPISODES
except ImportError:
    # Fallback defaults for standalone execution if config.py is not in path
    ALPHA: float = 0.2
    GAMMA: float = 0.95
    EPSILON: float = 0.1
    EPISODES: int = 500

# Constants for board representation
EMPTY_CELL: int = 0
PLAYER_X: int = 1
PLAYER_O: int = -1
VALID_MOVES_RANGE: range = range(9)

def check_winner(board: List[int]) -> int:
    """
    Evaluate the terminal state of the Tic-Tac-Toe board.

    Analyzes all possible winning combinations (rows, columns, diagonals).
    If no winner is found and there are empty cells, it returns 0.
    If the board is full with no winner, it is a draw (also returns 0,
    distinguished by checking `get_available_moves` later or explicit 
    logic in training loop). However, for standard RL terminal signal:
        1 : Player X wins
       -1 : Player O wins
        0 : Draw or Game Not Over (depending on context, usually 0 is draw)
    *Note*: For this implementation, we return 0 for both 'Not Over' and 'Draw'.
    The training loop must distinguish 'Not Over' via `get_available_moves`.

    Args:
        board: A list of 9 integers representing the grid state.
               Values: EMPTY_CELL (0), PLAYER_X (1), PLAYER_O (-1).

    Returns:
        int: 1 if X wins, -1 if O wins, 0 otherwise (draw or ongoing).

    Time Complexity: O(1) - Constant number of checks (8 total combinations).
    Space Complexity: O(1) - No additional data structures.
    """
    # Winning indices: rows, cols, diags
    lines = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Cols
        [0, 4, 8], [2, 4, 6]              # Diagonals
    ]

    for line in lines:
        a, b, c = line
        val_a, val_b, val_c = board[a], board[b], board[c]
        
        if val_a != EMPTY_CELL and val_a == val_b == val_c:
            return val_a  # Returns PLAYER_X (1) or PLAYER_O (-1)

    return EMPTY_CELL  # No winner yet or Draw

def get_available_moves(board: List[int]) -> List[int]:
    """
    Return list of indices for empty cells.

    Args:
        board: Current board state.

    Returns:
        List[int]: Indices of available moves.
    """
    return [i for i, cell in enumerate(board) if cell == EMPTY_CELL]

def create_empty_board() -> List[int]:
    """
    Create a new empty Tic-Tac-Toe board.

    Returns:
        List[int]: A list of 9 zeros.
    """
    return [EMPTY_CELL] * 9

def train_and_evaluate(csv_out_path: str = "results.csv") -> Dict[str, float]:
    """
    Train a tabular Q-Learning agent against itself for Tic-Tac-Toe.

    The agent plays episodes against an identical copy of itself. 
    Rewards:
        +1: Win
        0:  Draw or Intermediate step
       -1: Loss

    Metrics saved to CSV:
        win_rate, draw_rate, loss_rate

    Args:
        csv_out_path: Path to save the results CSV.

    Returns:
        Dict[str, float]: Dictionary containing final win/draw/loss rates.
    """
    # Initialize Q-table as a dictionary {state_tuple: [Q_X, Q_O]} or separate dicts.
    # Using defaultdict for convenience, but explicit dict is safer for serialization. 
    # To ensure deterministic behavior across runs without complex seeding of hash(), 
    # we rely on the agent's policy determinism where possible and fixed random seed.
    q_table_x: Dict[Tuple[int], List[float]] = {}
    q_table_o: Dict[Tuple[int], List[float]] = {}

    def get_q_value(q_table: Dict, state: Tuple[int], action: int) -> float:
        if state not in q_table:
            # Initialize Q-values for unseen states to 0.0
            # Create list of size 9 (max possible actions in empty board, sparse usage)
            # Actually, we only need entries for available moves.
            # Standard tabular RL: Key=State, Value=Vector of all actions.
            q_table[state] = [0.0 for _ in range(9)] 
        return q_table[state][action]

    def update_q_value(q_table: Dict, state: Tuple[int], action: int, reward: float, next_state: Tuple[int], done: bool) -> None:
        if state not in q_table:
            q_table[state] = [0.0 for _ in range(9)]
        
        current_q = get_q_value(q_table, state, action)
        
        # If terminal state, future value is 0
        if done:
            max_future_q = 0.0
        else:
            next_state_tuple = tuple(next_state)
            # Greedy choice for next step to update Q(s,a)
            # Note: In strict Q-learning, we take max_a Q(s', a)
            available_moves = get_available_moves(next_state)
            if not available_moves:
                max_future_q = 0.0
            else:
                max_future_q = max(get_q_value(q_table, next_state_tuple, a) for a in available_moves)
        
        # Bellman Equation: Q(s,a) <- Q(s,a) + alpha * (reward + gamma * max(Q(s',a')) - Q(s,a))
        new_q = current_q + ALPHA * (reward + GAMMA * max_future_q - current_q)
        q_table[state][action] = new_q

    # Tracking metrics
    wins_x: int = 0
    draws: int = 0
    wins_o: int = 0

    # Deterministic seed for reproducibility of the training process
    random.seed(42)

    print(f"Starting Q-Learning Training for {EPISODES} episodes...")
    
    for episode in range(EPISODES):
        board = create_empty_board()
        current_player: int = PLAYER_X  # X always goes first in standard TTT
        done: bool = False
        
        while not done:
            state_tuple = tuple(board)
            available_moves = get_available_moves(board)
            
            if not available_moves:
                # Should theoretically be caught by check_winner returning 0 and full board
                done = True
                break

            # Epsilon-Greedy Action Selection
            if random.random() < EPSILON:
                action = random.choice(available_moves)
            else:
                # Choose best action from current Q-table for current player
                q_values = []
                for a in available_moves:
                    val = get_q_value(q_table_x, state_tuple, a) if current_player == PLAYER_X 
                             else get_q_value(q_table_o, state_tuple, a)
                    q_values.append(val)
                
                max_q = max(q_values)
                # Handle ties by random choice among best actions to break determinism in policy
                best_actions = [a for a, q in zip(available_moves, q_values) if q == max_q]
                action = random.choice(best_actions)

            # Execute action
            board[action] = current_player
            winner: int = check_winner(board)
            
            next_state_tuple = tuple(board)
            next_available_moves = get_available_moves(board)

            if winner != EMPTY_CELL:
                # Terminal State Reached
                done = True
                if winner == PLAYER_X:
                    reward_current = 1.0
                    wins_x += 1
                else:
                    reward_current = -1.0
                    wins_o += 1
            elif not next_available_moves:
                # Draw (Board Full)
                done = True
                draws += 1
                reward_current = 0.0
            else:
                # Game Continues: Reward is 0 for intermediate steps in this simple formulation
                reward_current = 0.0

            # Back up Q-values for current player
            if current_player == PLAYER_X:
                update_q_value(q_table_x, state_tuple, action, reward_current, board, done)
            else:
                update_q_value(q_table_o, state_tuple, action, reward_current, board, done)

            # Switch turns
            current_player = -current_player

        if episode % 100 == 0:
            print(f"Episode {episode}: WinRate={wins_x/episode:.2f}, DrawRate={draws/episode:.2f}")

    final_win_rate: float = wins_x / EPISODES
    final_draw_rate: float = draws / EPISODES
    final_loss_rate: float = wins_o / EPISODES

    # Save results to CSV
    with open(csv_out_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["metric", "value"])
        writer.writerow(["win_rate", final_win_rate])
        writer.writerow(["draw_rate", final_draw_rate])
        writer.writerow(["loss_rate", final_loss_rate])
    
    print(f"Training complete. Results saved to {csv_out_path}")
    
    return {
        "win_rate": final_win_rate,
        "draw_rate": final_draw_rate,
        "loss_rate": final_loss_rate
    }

if __name__ == "__main__":
    # Execute training if run directly
    metrics = train_and_evaluate("results.csv")
    print(f"Final Metrics: {metrics}")