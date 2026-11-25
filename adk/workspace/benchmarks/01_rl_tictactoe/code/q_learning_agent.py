"""Implements the Q-Learning agent with epsilon-greedy exploration and tabular policy updates for finite-state environments."""
import random
import numpy as np
from typing import List, Dict, Tuple

BOARD_SIZE: int = 9

class QLearningAgent:
    """A class representing an agent that learns a policy using tabular Q-Learning."""
    q_table: Dict[Tuple[int, ...], np.ndarray]
    learning_rate: float
    discount_factor: float
    epsilon: float
    initial_epsilon: float
    decay: float

    def __init__(self, learning_rate: float, discount_factor: float, initial_epsilon: float, decay: float) -> None:
        """Initializes the agent with hyperparameters and creates an empty Q-table."""
        self.q_table = {}
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.initial_epsilon = initial_epsilon
        self.decay = decay
        self.epsilon = initial_epsilon

    def act(self, state: np.ndarray | Tuple[int, ...], valid_moves: List[int]) -> int:
        """Returns an integer action index from valid_moves using epsilon-greedy policy.

        Args:
            state: The game board state as a tuple or numpy array.
            valid_moves: A list of valid move indices.

        Returns:
            int: The selected action index.
        """
        if isinstance(state, np.ndarray):
            state_tuple = tuple(int(x) for x in state.tolist())
        elif isinstance(state, tuple):
            state_tuple = tuple(int(x) for x in state)
        else:
            raise ValueError(f'State must be a numpy array or tuple, got {type(state).__name__}')
        
        if state_tuple not in self.q_table:
            self.q_table[state_tuple] = np.zeros(BOARD_SIZE)
        
        q_values = self.q_table[state_tuple]
        
        # Ensure Q-values array is of correct size BOARD_SIZE
        if len(q_values) != BOARD_SIZE:
            new_q_values = np.zeros(BOARD_SIZE)
            if hasattr(self, 'q_table') and state_tuple in self.q_table:
                min_len = min(len(new_q_values), len(q_values))
                new_q_values[:min_len] = q_values[:min_len]
                self.q_table[state_tuple] = new_q_values
                q_values = new_q_values
        
        if random.random() < self.epsilon:
            return random.choice(valid_moves)
        
        valid_q = [q_values[m] for m in valid_moves]
        max_q_val = float(np.max(valid_q))
        best_idx_in_valid = int(np.argmax(valid_q))
        return valid_moves[best_idx_in_valid]

    def learn(self, state: np.ndarray | Tuple[int, ...], action: int, reward: float, next_state: np.ndarray | Tuple[int, ...], terminated: bool) -> None:
        """Updates the Q-value for the state-action pair using the Bellman equation."""
        if isinstance(state, np.ndarray):
            state_tuple = tuple(int(x) for x in state.tolist())
        elif isinstance(state, tuple):
            state_tuple = tuple(int(x) for x in state)
        else:
            raise ValueError(f'State must be a numpy array or tuple, got {type(state).__name__}')
        
        if state_tuple not in self.q_table:
            self.q_table[state_tuple] = np.zeros(BOARD_SIZE)

        q_values_state = self.q_table[state_tuple]
        # Ensure q_values_state is BOARD_SIZE long to safely index 'action'
        if len(q_values_state) != BOARD_SIZE:
            new_q_state = np.zeros(BOARD_SIZE)
            min_len = min(len(new_q_state), len(q_values_state))
            new_q_state[:min_len] = q_values_state[:min_len]
            self.q_table[state_tuple] = new_q_state
            q_values_state = new_q_state

        q_current = q_values_state[action]
        
        if terminated:
            target = reward
        else:
            if isinstance(next_state, np.ndarray):
                next_state_tuple = tuple(int(x) for x in next_state.tolist())
            elif isinstance(next_state, tuple):
                next_state_tuple = tuple(int(x) for x in next_state)
            else:
                raise ValueError(f'Next state must be a numpy array or tuple, got {type(next_state).__name__}')
            
            max_q_next = 0.0
            if next_state_tuple in self.q_table:
                q_values_next = self.q_table[next_state_tuple]
                # Ensure next Q-values are BOARD_SIZE long
                if len(q_values_next) != BOARD_SIZE:
                    new_q_next = np.zeros(BOARD_SIZE)
                    min_len_n = min(len(new_q_next), len(q_values_next))
                    new_q_next[:min_len_n] = q_values_next[:min_len_n]
                    self.q_table[next_state_tuple] = new_q_next
                    q_values_next = new_q_next
                max_q_next = float(np.max(q_values_next))
            
            target = reward + self.discount_factor * max_q_next
        
        new_q = q_current + self.learning_rate * (target - q_current)
        # Update the main Q-table entry again to ensure consistency after potential resize above
        if state_tuple not in self.q_table or len(self.q_table[state_tuple]) != BOARD_SIZE:
             self.q_table[state_tuple] = np.zeros(BOARD_SIZE)
        self.q_table[state_tuple][action] = new_q

    def reset(self) -> None:
        """Resets the internal exploration rate epsilon to initial_epsilon."""
        self.epsilon = self.initial_epsilon
