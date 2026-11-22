"""Tabular Q-Learning agent implementation for Tic-Tac-Toe."""
from __future__ import annotations
import copy
import random
from typing import Dict, List, Optional, Tuple
import numpy as np
DEFAULT_LEARNING_RATE: float = 0.1
DEFAULT_DISCOUNT_FACTOR: float = 0.95
DEFAULT_EPSILON: float = 0.1

class QLearningAgent:
    """
    Implements a Tabular Q-Learning agent with epsilon-greedy exploration.

    The Q-table maps hashable state representations (tuples of integers) to lists
    of action values (one per possible move index 0-8).
    """
    lr: 'float'
    gamma: 'float'
    epsilon: 'float'

    def __init__(self, lr: float=DEFAULT_LEARNING_RATE, gamma: float=DEFAULT_DISCOUNT_FACTOR, epsilon: float=DEFAULT_EPSILON) -> None:
        """
    Initialize the Q-Learning agent.

    Args:
        lr: The learning rate (alpha).
        gamma: The discount factor.
        epsilon: The exploration probability.
    """
        self.lr: float = lr
        self.gamma: float = gamma
        self.epsilon: float = epsilon
        self.q_table: Dict[Tuple[int, ...], List[float]] = {}

    def act(self, state: np.ndarray | str, valid_actions: list[int]) -> int:
        """
Select an action based on the current state using epsilon-greedy policy.

Args:
state: The current environment observation as a numpy array or string key.
valid_actions: A list of integer action indices that are legal in the current state.

Returns:
An integer from `valid_actions` representing the chosen move index.
"""
        if isinstance(state, str):
            state_key: tuple[int, ...] = state
        else:
            state_key = tuple(map(int, state))
        if state_key not in self.q_table:
            self.q_table[state_key] = [0.0] * 9
        if random.random() < self.epsilon:
            return random.choice(valid_actions)
        q_values = self.q_table[state_key]
        best_action_idx: int = valid_actions[0]
        max_q_val: float = q_values[best_action_idx]
        for action_idx in valid_actions[1:]:
            q_val = q_values[action_idx]
            if q_val > max_q_val:
                max_q_val = q_val
                best_action_idx = action_idx
        return best_action_idx

    def learn(self, state: np.ndarray | str, action: int, reward: float, next_state: np.ndarray | str, done: bool, valid_actions_next: list[int]) -> None:
        """
Perform a Q-Learning update step (Bellman equation).

Args:
state: The state before the action as a numpy array or string key.
action: The integer action taken in 'state'.
reward: The immediate reward received after taking 'action'.
next_state: The resulting state after 'action' as a numpy array or string key.
done: Boolean indicating if the episode has terminated.
valid_actions_next: A list of integer action indices that are legal in `next_state`.
"""
        if isinstance(state, str):
            s_key = state
        else:
            s_key = tuple(map(int, state))
        if isinstance(next_state, str):
            ns_key = next_state
        else:
            ns_key = tuple(map(int, next_state))
        if s_key not in self.q_table:
            self.q_table[s_key] = [0.0] * 9
        if ns_key not in self.q_table:
            self.q_table[ns_key] = [0.0] * 9
        current_q = self.q_table[s_key][action]
        if done:
            target = reward
        else:
            max_next_q = -float('inf')
            for a_next in valid_actions_next:
                q_next = self.q_table[ns_key][a_next]
                if q_next > max_next_q:
                    max_next_q = q_next
            if max_next_q == -float('inf'):
                target = reward
            else:
                target = reward + self.gamma * max_next_q
        self.q_table[s_key][action] += self.lr * (target - current_q)

    def q_table(self) -> Dict[Tuple[int, ...], List[float]]:
        """
    Return a copy of the internal Q-table.

    Returns:
        A dictionary mapping state representations (tuples of ints) to lists of Q-values (floats).
    """
        return copy.deepcopy(self.q_table)
