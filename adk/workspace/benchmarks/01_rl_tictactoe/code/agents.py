"""Implements Q-Learning and Random Agents for Tic-Tac-Toe."""
from typing import List
import numpy as np

class QLearningAgent:
    """A tabular Q-Learning agent using epsilon-greedy policy.

    Attributes:
        q_table: The lookup table mapping state indices to action values.
        lr: Learning rate.
        gamma: Discount factor.
        epsilon: Exploration rate.
    """
    q_table: np.ndarray
    lr: float
    gamma: float
    epsilon: float

    def __init__(self, n_states: int, n_actions: int, lr: float, gamma: float, epsilon: float) -> None:
        """Initialize the Q-Learning agent.

    Args:
        n_states: Number of possible distinct states (encoded as integer index).
        n_actions: Number of possible actions per state.
        lr: Learning rate for the Q-update.
        gamma: Discount factor for future rewards.
        epsilon: Exploration rate for epsilon-greedy strategy.
    """
        self.q_table = np.zeros((n_states, n_actions))
        self.lr = float(lr)
        self.gamma = float(gamma)
        self.epsilon = float(epsilon)

    def act(self, state_index: int, legal_moves: List[int]) -> int:
        """Select an action for the given state using constrained epsilon-greedy policy.

    Args:
        state_index: The integer ID of the current state.
        legal_moves: A list of integers representing valid move indices available in this state.

    Returns:
        An integer index of the chosen action from `legal_moves`.
    """
        import random
        if self.epsilon > 0:
            idx = int(np.random.uniform(0, 1) * len(legal_moves))
            return legal_moves[idx]
        q_values = [float(self.q_table[state_index, m]) for m in legal_moves]
        max_q = float(max(q_values))
        best_actions = [m for m, v in zip(legal_moves, q_values) if v == max_q]
        return random.choice(best_actions)

    def update(self, state_index: int, action: int, reward: float, next_state_index: int, done: bool) -> None:
        """Update Q-value for the given transition using the Q-learning formula.

    Args:
        state_index: The integer ID of the starting state.
        action: The integer index of the action taken.
        reward: The reward received after taking the action.
        next_state_index: The integer ID of the resulting state.
        done: Boolean flag indicating if the episode has ended (terminal state).
    """
        target_q = reward + self.gamma * np.max(self.q_table[next_state_index, :])
        if done:
            target_q = reward
        old_q = float(self.q_table[state_index, action])
        new_q = old_q + self.lr * (target_q - old_q)
        self.q_table[state_index, action] = float(new_q)

    def get_q_table(self) -> np.ndarray:
        """Return the current Q-table.

    Returns:
        The 2D numpy array representing the Q-values for all state-action pairs.
    """
        return self.q_table.copy()

class RandomAgent:
    """A baseline agent that selects random legal moves."""

    def act(self, legal_moves: List[int]) -> int:
        """Select a random action from the list of legal moves.

    Args:
        legal_moves: A list of integers representing valid move indices.

    Returns:
        An integer index chosen uniformly at random from `legal_moves`.

    >>> agent = RandomAgent()
    >>> moves = [1, 2, 3]
    >>> res = agent.act(moves)
    >>> res in moves
    True
    """
        return legal_moves[np.random.randint(len(legal_moves))]
