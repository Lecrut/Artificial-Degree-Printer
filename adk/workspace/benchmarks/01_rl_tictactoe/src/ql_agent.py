"""Module implementing a Tabular Q-Learning agent."""
from collections import defaultdict
import numpy as np
from typing import Dict, List, Tuple, Optional
ALPHA: float = 0.1
GAMMA: float = 0.9
EPSILON_START: float = 1.0
EPSILON_END: float = 0.01
DECAY_RATE: float = 0.95
EPOCHES_PER_DECAY_STEP: int = 10
N_EPISODES_PER_RUN: int = 100
RANDOM_SEED: int = 42
METRICS_TO_REPORT: List[str] = ['win_rate_agent', 'draw_rate', 'loss_rate_agent', 'average_reward_per_episode']
OUTPUT_CSV: str = 'results.csv'

def _hash_state_to_str(state_tuple: Tuple) -> str:
    """Convert a state tuple to a consistent hashable string key."""
    return '|'.join([str(x) for x in sorted(state_tuple)])

class QAgent:
    """A tabular Q-Learning agent with epsilon-greedy exploration."""

    def __init__(self, alpha: float=ALPHA, gamma: float=GAMMA, epsilon_start: float=EPSILON_START, epsilon_end: float=EPSILON_END, decay_rate: float=DECAY_RATE) -> None:
        """Initialize Q-table and hyperparameters."""
        self.Q_table: Dict[str, np.ndarray] = defaultdict(lambda: 0.0)
        self.epsilon: float = epsilon_start
        self.learning_rate: float = alpha
        self.discount_factor: float = gamma
        self.decay_rate: float = decay_rate
        self.total_episodes: int = 0

    def get_action(self, state_key: str) -> int:
        """Select an action using epsilon-greedy policy for the given state."""
        if state_key not in self.Q_table:
            self.Q_table[state_key] = np.zeros(3)
        if np.random.rand() < self.epsilon:
            return int(np.random.randint(3))
        else:
            q_values = self.Q_table[state_key]
            max_q = np.max(q_values)
            actions_with_max_q = [i for i, q in enumerate(q_values) if q == max_q]
            return int(actions_with_max_q[0]) if actions_with_max_q else int(np.random.randint(3))

    def update(self, state_key: str, action: int, reward: float, next_state_key: str) -> None:
        """Update the Q-value for the state-action pair using the Bellman equation."""
        if state_key not in self.Q_table:
            self.Q_table[state_key] = np.zeros(3)
        if next_state_key not in self.Q_table:
            self.Q_table[next_state_key] = np.zeros(3)
        current_q = self.Q_table[state_key][action]
        max_next_q = np.max(self.Q_table[next_state_key])
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_next_q - current_q)
        self.Q_table[state_key][action] = new_q

    def decay_epsilon(self) -> None:
        """Decrease epsilon by the decay rate towards epsilon_end."""
        self.epsilon = max(self.epsilon * self.decay_rate, self.epsilon_end)
from collections import defaultdict
