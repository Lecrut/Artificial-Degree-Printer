"""Q-Learning agent implementation for Tic-Tac-Toe."""
from typing import Callable, Dict, List, Literal
import numpy as np

class Q_Learning_Agent:
    """Implements a tabular Q-Learning agent for playing Tic-Tac-Toe against a random opponent."""

    def __init__(self, state_encoder: Callable[[list[int]], int], discount_factor: float=0.99, learning_rate: float=0.1, epsilon_start: float=1.0, epsilon_end: float=0.0, epsilon_decay: float=0.995, epsilon_min_steps_to_end: int=2000) -> None:
        """Initialize the Q-Learning agent.

Args:
    state_encoder: Function mapping a board configuration to a unique integer ID.
    discount_factor: Gamma for future rewards (default 0.99).
    learning_rate: Alpha for Q-value updates (default 0.1).
    epsilon_start: Initial exploration probability (default 1.0).
    epsilon_end: Minimum exploration probability (default 0.0).
    epsilon_decay: Decay rate for epsilon schedule (default 0.995).
    epsilon_min_steps_to_end: Steps after which epsilon reaches zero (default 2000).

Returns:
    None.
    """
        self.Q_table: Dict[int, Dict[int, float]] = {}
        self.discount_factor: float = discount_factor
        self.learning_rate: float = learning_rate
        self.epsilon_start: float = epsilon_start
        self.epsilon_end: float = epsilon_end
        self.epsilon_decay: float = epsilon_decay
        self.epsilon_min_steps_to_end: int = epsilon_min_steps_to_end
        self.current_state_index: int = 0
        super().__init__()

    def reset(self) -> int:
        """Reset the agent's internal state and return the initial state index."""
        initial_state = [0] * 9
        self.current_state_index = self.state_encoder(initial_state)
        return self.current_state_index

    def select_action(self, state_index: int) -> int:
        """Select an action based on Epsilon-Greedy policy.

    Args:
        state_index: The unique integer ID of the current board state.

    Returns:
        The integer action index (0 to 8) representing placing a marker in that cell, or -1 if no move valid. If Q values are insufficient for exploitation, returns random available action.
    """
        steps_elapsed = self.current_state_index
        current_epsilon: float = self.epsilon_start
        if self.epsilon_min_steps_to_end > 0:
            decay_factor = self.epsilon_decay ** min(steps_elapsed, self.epsilon_min_steps_to_end)
            current_epsilon = max(self.epsilon_end, self.epsilon_start * decay_factor)
        if state_index not in self.Q_table or not self.Q_table[state_index]:
            return np.random.randint(0, 9)
        q_values = self.Q_table[state_index]
        max_q_value = max(q_values.values())
        candidates = [a for a, v in q_values.items() if v == max_q_value]
        if np.random.uniform() < current_epsilon:
            return np.random.choice(candidates)
        return int(np.random.choice(candidates))

    def update(self, state_index: int, action: int, reward: float, next_state_index: int) -> None:
        """Update the Q-value for a given state-action pair.

    Args:
        state_index: Unique ID of the current state.
        action: Action taken in the current state.
        reward: Scalar reward received after taking the action.
        next_state_index: Unique ID of the next state reached.

    Returns:
        None. Updates self.Q_table in place using Q-learning update rule.
    """
        if state_index not in self.Q_table:
            self.Q_table[state_index] = {}
        if action not in self.Q_table[state_index]:
            self.Q_table[state_index][action] = 0.0
        current_q: float = self.Q_table[state_index][action]
        if next_state_index not in self.Q_table:
            max_next_q: float = 0.0
        else:
            max_next_q = max(self.Q_table[next_state_index].values())
        target_value: float = reward + self.discount_factor * max_next_q
        new_q: float = current_q + self.learning_rate * (target_value - current_q)
        self.Q_table[state_index][action] = new_q

    def train_episode(self, opponent_func: Callable[[int], int]) -> None:
        """Train the agent in a single episode against the given opponent.

    Args:
        opponent_func: Function mapping current state index to the opponent's action index.

    Returns:
        None. Trains the agent for one full game until terminal or draw.
    """
        done = False
        total_reward = 0.0
        while not done:
            action: int = self.select_action(self.current_state_index)
            reward, next_state, done = self.game_env.step(action)
            total_reward += reward
            self.current_state_index = next_state
            if done:
                break
            self.update(self.current_state_index, action, reward, next_state_index=next_state)

    def state_encoder(self, state: list[int]) -> int:
        """
    Map the board state to a single integer index for the Q-table.

    Returns:
        int: A deterministic hash based on the board configuration.
    """
        return hash(tuple(state))
