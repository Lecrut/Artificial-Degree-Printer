"""Implements the Tabular Q-Learning agent with an epsilon-greedy policy for finite-state environments."""
import numpy as np
from typing import Optional

class QLearningAgent:
    """A tabular Q-Learning agent that maintains a Q-table of values for state-action pairs and updates them using the Bellman equation."""
    q_values: np.ndarray

    def __init__(self, num_states: int, num_actions: int, lr: float=0.1, gamma: float=0.9, epsilon: float=1.0) -> None:
        """Initializes the Q-table to zeros and sets hyperparameters.

    Args:
        num_states: The total number of possible states in the environment.
        num_actions: The size of the action space (total possible actions, e.g., 9 for Tic-Tac-Toe).
        lr: The learning rate for Q-value updates.
        gamma: The discount factor for future rewards.
        epsilon: The initial exploration rate for the epsilon-greedy policy."""
        self.q_values: np.ndarray = np.zeros((num_states, num_actions))
        self.lr: float = lr
        self.gamma: float = gamma
        self.epsilon: float = epsilon

    def choose_action(self, state: int, valid_actions: list[int]) -> Optional[int]:
        """Selects an action using an epsilon-greedy policy, respecting validity constraints.

    If a random number is less than epsilon, returns a random action chosen uniformly from `valid_actions`. Otherwise,
    returns the action with the highest Q-value among `valid_actions` (breaking ties by index). If `valid_actions` is empty, returns None.

    Args:
        state: The current state index.
        valid_actions: A list of integer indices representing actions that are legal in the current state.

    Returns:
        Optional[int]: The selected action index, or None if no valid actions exist."""
        if not valid_actions:
            return None
        if np.random.random() < self.epsilon:
            return int(np.random.choice(valid_actions))
        q_vals = self.q_values[state, valid_actions]
        max_q = np.max(q_vals)
        best_indices = np.where(q_vals == max_q)[0]
        best_valid_idx = valid_actions[best_indices[0]]
        return int(best_valid_idx)

    def update(self, state: int, action: int, reward: float, next_state: int, done: bool) -> None:
        """Updates the Q-value for the given state-action pair.

    Uses the standard Q-Learning update rule: 
        Q(s,a) <- Q(s,a) + lr * (reward + gamma * max(Q(next_s, :)) - Q(s,a))

    If the episode is done, the future value term is ignored (treated as 0).

    Args:
        state: The state index where the action was taken.
        action: The action index that was taken.
        reward: The immediate reward received after taking the action.
        next_state: The index of the subsequent state.
        done: Boolean indicating if the episode has terminated."""
        if done:
            td_target = reward
        else:
            td_target = reward + self.gamma * np.max(self.q_values[next_state])
        self.q_values[state, action] += self.lr * (td_target - self.q_values[state, action])

    def get_q_values(self) -> np.ndarray:
        """Returns a copy of the current Q-table.

    Returns:
        np.ndarray: A 2D array of shape (num_states, action_dim) containing the learned values."""
        return self.q_values.copy()
