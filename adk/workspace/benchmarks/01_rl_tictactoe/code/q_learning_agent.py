"""
Q-Learning agent implementation.
Uses a hashable state key to index actions in the Q-table.
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
import config

class QLearner:
    """
    Q-Learning agent with standard hyperparameters for Tic-Tac-Toe.
    """

    def __init__(self) -> None:
        """
    Initialize the Q-Learning agent with parameters from config.py.
    Sets up the Q-table as empty and initializes learning rates.
    """
        self.q_table: Dict[Tuple[int, ...], Dict[int, float]] = {}
        self.alpha: float = config.ALPHA
        self.gamma: float = config.GAMMA
        self.epsilon: float = config.EPSILON

    def choose_action(self, state_key: Tuple[int, int]) -> int:
        """
        Select an action using epsilon-greedy policy.
        Args:
            state_key: The canonical key for the current state (tuple of length 2).
        Returns:
            Index of the chosen action (0-8).
        """
        if len(state_key) != 2:
            raise ValueError(f'State key must be a tuple of length 2, got {len(state_key)}')
        actions: List[int] = list(range(9))
        if self.Q_table.get(state_key) is None:
            return np.random.choice(actions)
        state_Q_values: Dict[int, float] = self.Q_table[state_key]
        max_q: float = max(state_Q_values.values())
        best_actions: List[int] = [a for a, q in state_Q_values.items() if abs(q - max_q) < 1e-06]
        epsilon_threshold: float = config.EPSILON_MIN
        if self.epsilon >= epsilon_threshold:
            if np.random.rand() < self.epsilon:
                return np.random.choice(actions)
            else:
                return best_actions[np.random.randint(len(best_actions))]
        return best_actions[0]

    def update(self, state_key: Tuple[int, int], action: int, reward: float, next_state_key: Tuple[int, int]) -> None:
        """
        Perform a Q-learning update step.
        Args:
            state_key: Current state key (tuple of length 2).
            action: Chosen action index (0-8).
            reward: Received scalar reward.
            next_state_key: Key of the resulting state (tuple of length 2).
        """
        if len(state_key) != 2 or len(next_state_key) != 2:
            raise ValueError('State keys must be tuples of length 2')
        if self.Q_table.get(state_key) is None:
            self.Q_table[state_key] = {action: 0.0}
        current_q: float = self.Q_table[state_key][action]
        next_Q_value: float = 0.0
        if self.Q_table.get(next_state_key) is not None:
            next_Q_values = list(self.Q_table[next_state_key].values())
            next_Q_value = max(next_Q_values)
        target_q: float = reward + self.gamma * next_Q_value
        current_q += self.alpha * (target_q - current_q)
        if self.epsilon >= config.EPSILON_MIN:
            decayed_epsilon: float = max(config.EPSILON_MIN, self.epsilon * config.EPSILON_DECAY_RATE)
            self.epsilon = decayed_epsilon
        else:
            self.epsilon = config.EPSILON_MIN

    def get_all_actions(self, state_key: Tuple[int, int]) -> List[int]:
        """
        Get all possible actions for a given state key.
        Args:
            state_key: Current state (tuple of length 2).
        Returns:
            List of integers representing action indices (0-8).
        """
        return list(range(9))
