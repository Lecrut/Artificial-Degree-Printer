"""Tabular Q-Learning Agent implementation."""
from typing import Dict, List, Tuple
import numpy as np

class QAgent:
    """Q-Learning agent using a tabular approximation.

    Attributes:
        lr: Learning rate (alpha).
        gamma: Discount factor (gamma).
        epsilon: Exploration rate.

    Behaviors:
        - Select action using epsilon-greedy policy.
          >>> agent = QAgent(epsilon=1.0)
          >>> import random
          >>> random.seed(42)
          >>> valid = [0, 1]
          >>> _ = agent.act((0,)*9, valid)
        - Update Q-value for the given transition.
          >>> agent = QAgent(lr=0.1)
          >>> s = (0,)*9
          >>> ns = (1,)+ (0,)*8  # Correctly create a new tuple
          >>> agent.learn(s, 0, 0.1, ns)
    """

    def __init__(self, lr: float=0.1, gamma: float=0.9, epsilon: float=0.2) -> None:
        """Initialize Q-agent.

        Args:
            lr: Learning rate (alpha).
            gamma: Discount factor (gamma).
            epsilon: Exploration rate.

        Returns:
            None.
        """
        self.lr = lr
        self.gamma = gamma
        self.epsilon = epsilon
        self.q_table: Dict[Tuple[int, ...], Dict[int, float]] = {}

    def act(self, state: Tuple[int, ...], valid_actions: List[int]) -> int:
        """Select action using epsilon-greedy policy.

        Args:
            state: Current state as a tuple of integers.
            valid_actions: List of allowed action indices.

        Returns:
            An integer index of the chosen action.
        """
        if not self.q_table.get(state):
            return int(np.random.choice(valid_actions))
        q_values = self.q_table[state]
        best_q = max(q_values.values())
        best_actions = [a for a, v in q_values.items() if v == best_q]
        if np.random.random() < self.epsilon:
            return int(np.random.choice(valid_actions))
        return int(best_actions[0])

    def learn(self, state: Tuple[int, ...], action: int, reward: float, next_state: Tuple[int, ...]) -> None:
        """Update Q-value for the given transition.

    Args:
        state: Current state as a tuple of integers.
        action: Index of the taken action.
        reward: Immediate reward received.
        next_state: Next state as a tuple of integers.

    Returns:
        None.
    """
        if state not in self.q_table:
            self.q_table[state] = {}
        q_old = self.q_table[state].get(action, 0.0)
        if next_state not in self.q_table:
            self.q_table[next_state] = {}
        max_next_q: float = -np.inf
        for a_n, row in self.q_table.items():
            try:
                q_for_a = row.get(a_n[0], 0.0)
            except (IndexError, TypeError):
                q_for_a = 0.0
            if q_for_a > max_next_q:
                max_next_q = q_for_a
        target = reward + self.gamma * max_next_q if max_next_q != -np.inf else reward
        new_q = q_old + self.lr * (target - q_old)
        self.q_table[state][action] = new_q
