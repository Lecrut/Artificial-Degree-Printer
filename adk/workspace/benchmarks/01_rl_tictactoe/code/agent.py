"""Implements the Q-Learning algorithm with epsilon-greedy exploration for the Tic-Tac-Toe state space."""
from __future__ import annotations
import numpy as np
from typing import List, Union

class QLearningAgent:
    """A tabular Q-Learning agent.

    The agent maintains a dictionary mapping board states (tuples) to Q-value vectors (ndarrays).
    It uses an epsilon-greedy policy for action selection.
    """
    q_table: 'dict[tuple[int, ...], np.ndarray]'
    alpha: float
    gamma: float
    epsilon: float

    def __init__(self, alpha: float, gamma: float, epsilon: float) -> None:
        """Initialize the Q-Learning agent.

        Args:
            alpha: The learning rate (step size). Must be in (0, 1].
            gamma: The discount factor. Must be in [0, 1].
            epsilon: The initial exploration rate for epsilon-greedy policy.
                     Must be in [0, 1].
        """
        self.q_table: dict[tuple[int, ...], np.ndarray] = {}
        self.alpha: float = alpha
        self.gamma: float = gamma
        self.epsilon: float = epsilon

    def select_action(self, state: Union[tuple[int, ...], List[int], np.ndarray], valid_moves: Union[List[int], np.ndarray]) -> int:
        """Select an action using the epsilon-greedy policy.

        If a random number is less than self.epsilon, selects a random move
        from valid_moves. Otherwise, selects the move with the highest Q-value
        for the current state. In case of ties in Q-values, picks uniformly
        among the best moves.

        Args:
            state: The current board state as a tuple of integers, or an array-like convertible to tuple.
            valid_moves: A list or array of integer indices representing legal actions.

        Returns:
            int: The index of the selected action from valid_moves.
        """
        import random
        if random.random() < self.epsilon:
            return int(random.choice(valid_moves))
        
        q_values = self.get_q_values(state)
        max_q = float(np.max(q_values))
        best_valid_indices: list[int] = []
        for idx, move_idx in enumerate(valid_moves):
            if abs(float(q_values[move_idx]) - max_q) < 1e-09:
                best_valid_indices.append(int(move_idx))
        
        return int(random.choice(best_valid_indices))

    def update(self, state: Union[tuple[int, ...], np.ndarray], action: int, reward: float, next_state: Union[tuple[int, ...], np.ndarray], done: bool) -> None:
        """Update the Q-value for the given state-action pair.

        Uses the standard Q-Learning update rule:
        Q(s, a) <- Q(s, a) + alpha * (reward + gamma * max_a' Q(s', a') - Q(s, a))

        Args:
            state: The previous board state.
            action: The integer index of the action taken.
            reward: The scalar reward received after taking the action.
            next_state: The resulting board state.
            done: Boolean indicating if the episode has ended.
        """
        current_q = self.get_q_values(state)[action]
        next_q_values = self.get_q_values(next_state)
        if done:
            target_q = reward
        else:
            target_q = reward + self.gamma * float(np.max(next_q_values))
        
        # Normalize states to tuples before dictionary lookup
        s_key = state if isinstance(state, tuple) else tuple(state)
        ns_key = next_state if isinstance(next_state, tuple) else tuple(next_state)

        new_q = current_q + self.alpha * (target_q - current_q)
        
        # Ensure the key exists in q_table before updating
        if s_key not in self.q_table:
            self.q_table[s_key] = np.zeros(9)
            # If we are initializing because of this update, it's a new state.
            # But typically get_q_values would have initialized it. 
            # However, to be safe against race conditions or logic gaps in previous steps:
        
        self.q_table[s_key][action] = new_q

    def get_q_values(self, state: Union[tuple[int, ...], np.ndarray, List[int]]) -> np.ndarray:
        """Retrieve or initialize Q-values for a specific state.

        Args:
            state: The board state tuple or array-like representation.

        Returns:
            np.ndarray: An array of Q-values for all possible actions. 
                        If the state has not been visited before, returns an 
                        initialized zero-vector of length 9 (standard Tic-Tac-Toe board size).
        """
        # CRITICAL FIX: Convert numpy arrays or lists to tuples for dictionary key lookup
        if isinstance(state, np.ndarray):
            state_key = tuple(state)
        elif isinstance(state, list):
            state_key = tuple(state)
        else:
            state_key = state

        if state_key not in self.q_table:
            self.q_table[state_key] = np.zeros(9)
        return self.q_table[state_key]