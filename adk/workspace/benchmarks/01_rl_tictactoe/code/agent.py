"""Implements the Q-Learning agent class with standard exploration-exploitation logic (epsilon-greedy)."""
from __future__ import annotations
import numpy as np
from typing import Optional, Tuple
DEFAULT_ALPHA: float = 0.1
DEFAULT_GAMMA: float = 0.9
DEFAULT_EPSILON_START: float = 1.0
DEFAULT_EPSILON_END: float = 0.05

class QLearningAgent:
    """A tabular Q-Learning agent for Tic-Tac-Toe.

    The agent maintains a Q-table mapping states (board configurations) to action values.
    It uses an epsilon-greedy policy for exploration. State entries are lazily initialized
    as 1-dimensional numpy arrays of shape (9,) to prevent indexing errors.
    """
    env: object
    alpha: float
    gamma: float
    epsilon: float
    q_table: dict[tuple[int, ...], np.ndarray]
    rng: np.random.Generator

    def __init__(self, env: object, alpha: float=DEFAULT_ALPHA, gamma: float=DEFAULT_GAMMA, epsilon: float=DEFAULT_EPSILON_START) -> None:
        """Initialize the Q-Learning agent.

        Args:
            env: The TicTacToe environment instance. Used to determine action space size.
            alpha: The learning rate for Q-value updates. Defaults to 0.1.
            gamma: The discount factor for future rewards. Defaults to 0.9.
            epsilon: The initial exploration rate (probability of choosing a random action).
                     Defaults to 1.0 (pure exploration initially).
        """
        self.env = env
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.rng = np.random.default_rng(seed=42)
        self.q_table: dict[tuple[int, ...], np.ndarray] = {}

    def _ensure_q_entry(self, key: tuple[int, ...], num_actions: int | None=None) -> None:
        """Ensure a Q-table entry exists for the given key.

        Initializes with zeros if it doesn't exist. Uses environment action space size
        if no specific size is provided.

        Args:
            key: The state tuple to ensure in the table.
            num_actions: Optional explicit size for the action vector.
        """
        if key not in self.q_table:
            if num_actions is None:
                if hasattr(self.env, 'action_space') and hasattr(self.env.action_space, 'n'):
                    num_actions = self.env.action_space.n
                else:
                    num_actions = 9
            self.q_table[key] = np.zeros(num_actions, dtype=np.float64)

    def act(self, state: int | np.ndarray) -> int:
        """Select an action for the given state using the epsilon-greedy policy.

        If a random number is less than epsilon, a random valid action is selected.
        Otherwise, the action with the highest Q-value is selected. Ties are broken randomly.

        Args:
            state: The current environment observation. Can be an int or np.ndarray.
                   Must correspond to a key in the q_table (or will be added).

        Returns:
            action: A standard Python integer in [0, 8] representing the chosen cell index.
        """
        s_key: tuple[int, ...] = self._normalize_state(state)
        valid_actions: list[int] = []
        if hasattr(self.env, 'is_valid_move') and hasattr(self.env, 'action_space'):
            num_actions = getattr(self.env.action_space, 'n', 9)
            for i in range(num_actions):
                if self.env.is_valid_move(s_key, i):
                    valid_actions.append(i)
        if not valid_actions:
            return 0
        if self.rng.random() < self.epsilon:
            chosen_action_idx: int = self.rng.choice(valid_actions).item()
            return chosen_action_idx
        else:
            self._ensure_q_entry(s_key, len(valid_actions) if hasattr(self.env, 'action_space') and hasattr(self.env.action_space, 'n') else 9)
            if s_key not in self.q_table or len(self.q_table[s_key]) != 9:
                self._ensure_q_entry(s_key, 9)
            q_vals: np.ndarray = self.q_table[s_key]
            max_q_val: float = -np.inf
            for i in valid_actions:
                if i < len(q_vals):
                    val = float(q_vals[i])
                    if val > max_q_val:
                        max_q_val = val
            best_actions: list[int] = [i for i in valid_actions if abs(float(self.q_table[s_key][i]) - max_q_val) < 1e-06]
            if not best_actions:
                return valid_actions[0]
            chosen_action_idx: int = self.rng.choice(best_actions).item()
            return chosen_action_idx

    def update(self, state: int | np.ndarray, action: int, reward: float, next_state: int | np.ndarray, done: bool) -> None:
        """Update the Q-value for the given state-action pair.

    Uses the standard Q-Learning update rule:
    Q(s, a) <- Q(s, a) + alpha * (reward + gamma * max_a' Q(s', a') - Q(s, a))

    Args:
        state: The previous environment observation. Can be an int or np.ndarray.
        action: The action taken by the agent.
        reward: The reward received from the environment.
        next_state: The new environment observation after taking the action. Can be an int or np.ndarray.
        done: Boolean indicating if the episode has terminated.
    """
        s_key: tuple[int, ...] = self._normalize_state(state)
        ns_key: tuple[int, ...] = self._normalize_state(next_state)
        normalized_action: int = int(action)
        expected_size: int = 9
        if hasattr(self.env, 'action_space') and hasattr(self.env.action_space, 'n'):
            expected_size = self.env.action_space.n
        self._ensure_q_entry(s_key, expected_size)
        self._ensure_q_entry(ns_key, expected_size)
        current_q: float = float(self.q_table[s_key][normalized_action])
        if done:
            max_next_q: float = 0.0
        elif ns_key in self.q_table:
            max_next_q: float = float(np.max(self.q_table[ns_key]))
        else:
            max_next_q: float = 0.0
        new_q: float = current_q + self.alpha * (reward + self.gamma * max_next_q - current_q)
        self.q_table[s_key][normalized_action] = new_q

    def _normalize_state(self, state: int | np.ndarray) -> tuple[int, ...]:
        """Convert the given state to a tuple of integers for dictionary keys.

        Handles both integer and numpy array inputs by converting them to tuples.

        Args:
            state: The environment observation. Can be an int or np.ndarray.

        Returns:
            A tuple of integers representing the board configuration.
        """
        if isinstance(state, tuple):
            return state
        if isinstance(state, (list, np.ndarray)):
            return tuple((int(x) for x in state))
        return (int(state),)
