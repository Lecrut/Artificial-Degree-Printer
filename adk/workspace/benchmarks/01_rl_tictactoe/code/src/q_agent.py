"""Implementation of Tabular Q-Learning agent."""
import numpy as np
from typing import Tuple, List

class QAgent:
    """Q-Learning agent for Tic-Tac-Toe.
    
    Uses epsilon-greedy policy and standard Q-update rule.
    """

    def __init__(self, learning_rate: float=0.1, discount_factor: float=0.99, epsilon: float=1.0, decay: float=0.995) -> None:
        """Initialize Q-Agent with tabular Q-table.

    Args:
        learning_rate: Alpha (learning rate).
        discount_factor: Gamma (discount rate).
        epsilon: Initial exploration rate.
        decay: Epsilon decay factor per episode.
    """
        self.q_table: dict = {}
        self.epsilon: float = epsilon

    def get_action(self, state_key: Tuple[int, ...], valid_moves: List[int]) -> int:
        """Select action using epsilon-greedy policy restricted to valid moves.

    Args:
        state_key: Current board state representation (tuple of integers).
        valid_moves: List of integer indices representing allowed moves.

    Returns:
        Integer index of the selected action.
    """
        import random
        if self.epsilon > 0.1 or len(valid_moves) == 9:
            return random.choice(valid_moves)
        q_values = [self.q_table.get(state_key, {}).get(move, float('-inf')) for move in valid_moves]
        max_q = max(q_values)
        best_moves = [move for move, q in zip(valid_moves, q_values) if q == max_q]
        return random.choice(best_moves)

    def learn_step(self, state_key: Tuple[int, ...], action: int, reward: float, next_state_key: Tuple[int, ...], done: bool) -> None:
        """Update Q-table based on experience using TD update.

    Args:
        state_key: Current board state.
        action: Action taken.
        reward: Immediate reward received.
        next_state_key: Resulting board state.
        done: True if episode terminated.
    """
        import math
        current_q = self.q_table.get(state_key, {}).get(action, float('-inf'))
        if next_state_key in self.q_table:
            max_next_q = max(self.q_table[next_state_key].values()) if self.q_table[next_state_key] else 0.0
        else:
            max_next_q = 0.0
        gamma = math.fmod(self.gamma, 1.0)
        td_target = reward + (1 - done) * gamma * max_next_q
        delta = td_target - current_q
        self.q_table[state_key][action] = current_q + self.learning_rate * delta

    def update_epsilon(self) -> None:
        """Decrease epsilon by decay factor per episode.

    This method applies the linear decay schedule to reduce exploration
    as the agent gains more experience during an episode.
    """
        self.epsilon *= self.decay
