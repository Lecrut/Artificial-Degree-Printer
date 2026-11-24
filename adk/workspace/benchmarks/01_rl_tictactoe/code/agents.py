"""Defines the Q-Learning agent with tabular update rules and the Random baseline opponent."""
from typing import Optional
import numpy as np
import environment

class QLearningAgent:
    """A tabular Q-Learning agent.

    The Q-table is a NumPy array of shape (STATE_SPACE_SIZE, 9).
    States are indexed using the base-3 encoding of the board configuration,
    mapping each unique board state to a row in the table.
    Uses epsilon-greedy action selection for exploration.

    Attributes:
        q_table: np.ndarray of shape (STATE_SPACE_SIZE, 9). The Q-values for each state-action pair.
        learning_rate: float. Step size for Q-value updates (alpha).
        discount_factor: float. Future reward discount factor (gamma).
        epsilon: float. Default exploration rate for epsilon-greedy policy.
    """
    learning_rate: 'object'
    discount_factor: 'object'
    epsilon: 'object'
    q_table: np.ndarray

    def __init__(self, learning_rate: float=0.1, discount_factor: float=0.95, epsilon: float=0.1) -> None:
        """Initialize the Q-Learning agent.

    Args:
        learning_rate: Step size for Q-value updates (alpha).
        discount_factor: Future reward discount factor (gamma).
        epsilon: Initial exploration rate for epsilon-greedy policy.
    """
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.q_table = np.zeros((environment.STATE_SPACE_SIZE, environment.ACTION_SPACE_SIZE))

    def _state_to_index(self, obs: np.ndarray) -> int:
        """Convert a board state array to a unique integer index.

    Encodes the 3x3 board (flattened to 9 cells) into a base-3 integer.
    Values in `obs` are treated as: -1 -> 0, 0 -> 1, 1 -> 2.

    Args:
        obs: np.ndarray of shape (9,), the current board state.

    Returns:
        int: A unique integer index in [0, environment.STATE_SPACE_SIZE).
    """
        encoded_state = np.where(obs == -1, 0, np.where(obs == 0, 1, 2))
        weights = np.array([3 ** (8 - i) for i in range(9)], dtype=int)
        index = int(np.sum(encoded_state * weights))
        return index

    def get_action(self, obs: np.ndarray, epsilon: Optional[float]=None) -> int:
        """Select an action based on the current state using epsilon-greedy policy.

    Args:
        obs: np.ndarray of shape (9,), the current board state.
        epsilon: float or None. Exploration rate. If None, uses self.epsilon.

    Returns:
        int: Action index in [0, 8].
    """
        if epsilon is None:
            eps = self.epsilon
        else:
            eps = epsilon
        state_idx = self._state_to_index(obs)
        actions = self.q_table[state_idx]
        if np.random.rand() < eps:
            return int(np.random.randint(0, environment.ACTION_SPACE_SIZE))
        else:
            return int(np.argmax(actions))

    def learn(self, obs: np.ndarray, action: int, reward: float, next_obs: np.ndarray, terminated: bool) -> None:
        """Update the Q-value for the observed transition.

    Performs a standard Q-Learning update:
    Q(s, a) <- Q(s, a) + alpha * (target - Q(s, a))
    where target is reward if terminated, else reward + gamma * max_a' Q(s', a').

    Args:
        obs: np.ndarray of shape (9,), the state before the action.
        action: int, the action taken.
        reward: float, the reward received.
        next_obs: np.ndarray of shape (9,), the state after the action.
        terminated: bool, True if the episode ended (terminal state).
    """
        current_q = self.q_table[self._state_to_index(obs), action]
        state_idx_next = self._state_to_index(next_obs)
        next_actions_q_max = np.max(self.q_table[state_idx_next])
        if terminated:
            target = reward
        else:
            target = reward + self.discount_factor * next_actions_q_max
        self.q_table[self._state_to_index(obs), action] += self.learning_rate * (target - current_q)

class RandomAgent:
    """A baseline agent that selects valid actions uniformly at random.

    Accepts legal actions to ensure only available cells are chosen,
    preventing invalid moves in Tic-Tac-Toe.
    """

    def get_action(self, obs: np.ndarray, legal_actions: list[int]) -> int:
        """Select a random valid action index.

    Args:
        obs: np.ndarray of shape (9,), the current board state (unused for logic but kept for API compatibility).
        legal_actions: list[int]. The list of valid action indices in the current state.
                           Must contain at least one element. Passing an empty list raises ValueError.

    Returns:
        int: A valid action index from `legal_actions`.
    """
        if len(legal_actions) == 0:
            raise ValueError('No legal actions available.')
        return int(np.random.choice(legal_actions))
