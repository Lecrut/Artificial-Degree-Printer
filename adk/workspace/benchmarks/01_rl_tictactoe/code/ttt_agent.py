import math
import numpy as np
import random

class Agent:
    """Q-Learning agent for Tic-Tac-Toe."""

    def __init__(self, learning_rate: float=0.1, discount_factor: float=0.9, epsilon_start: float=1.0, epsilon_end: float=0.01, epsilon_decay: float=0.995, seed: int | None=None):
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon_start = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.epsilon = epsilon_start
        self.q_table: dict[str, list[float]] = {}
        if seed is not None:
            random.seed(seed)

    def reset(self) -> None:
        """Resets the agent's internal state (e.g., for a new game)."""
        self.epsilon = self.epsilon_start

    def get_q_values(self, state_hash: str) -> list[float]:
        """Retrieves Q-values for a specific state."""
        if state_hash not in self.q_table:
            return [0.0] * 9
        return list(self.q_table[state_hash])

    def choose_action(self, state_hash: str, legal_moves: list[int], epsilon: float) -> int:
        """Chooses an action based on epsilon-greedy policy."""
        if random.random() < epsilon:
            return random.choice(legal_moves)
        else:
            q_vals = self.get_q_values(state_hash)
            max_q = max((q_vals[i] for i in legal_moves))
            best_actions = [i for i in legal_moves if abs(q_vals[i] - max_q) < 1e-09]
            return random.choice(best_actions)

    def update(self, state_hash: str, action: int, reward: float, next_state_hash: str, done: bool) -> None:
        """Updates the Q-value for the given state-action pair."""
        if state_hash not in self.q_table:
            self.q_table[state_hash] = [0.0] * 9
        current_q = self.q_table[state_hash][action]
        if not done and next_state_hash in self.q_table:
            next_q_vals = self.get_q_values(next_state_hash)
            max_next_q = max(next_q_vals)
        else:
            max_next_q = 0.0
        if done:
            target = reward
        else:
            target = reward + self.gamma * max_next_q
        new_q = current_q + self.lr * (target - current_q)
        self.q_table[state_hash][action] = new_q
        self.decay_epsilon()

    def decay_epsilon(self) -> None:
        """Decreases epsilon by the decay factor, but not below epsilon_end."""
        self.epsilon *= self.epsilon_decay
        if self.epsilon < self.epsilon_end:
            self.epsilon = self.epsilon_end
