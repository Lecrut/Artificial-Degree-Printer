"""Implements a tabular Q-Learning agent with configurable epsilon-greedy exploration for Tic-Tac-Toe."""
import numpy as np
import os
from typing import Dict, List, Tuple

class QAgent:
    """A tabular Q-Learning agent that maintains a sparse Q-table (dictionary) indexed by state hashes and supports saving/loading."""
    q_table: Dict[Tuple[int, int], float]
    lr: float
    gamma: float
    epsilon: float
    epsilon_decay: float
    n_actions: int

    def __init__(self, n_actions: int, lr: float=0.1, gamma: float=0.9, epsilon: float=1.0, epsilon_decay: float=0.999) -> None:
        """Initializes the Q-agent with an empty sparse Q-table and specified hyperparameters. Args: n_actions - The number of possible actions (9). lr - The learning rate for the Bellman update. gamma - The discount factor for future rewards, set to 0.9 by default. epsilon - The initial exploration rate (probability of random action). epsilon_decay - The multiplicative decay factor applied to epsilon after each call to choose_action."""
        if lr < 0 or lr > 1:
            raise ValueError('lr must be between 0 and 1')
        if gamma < 0 or gamma > 1:
            raise ValueError('gamma must be between 0 and 1')
        if epsilon < 0 or epsilon > 1:
            raise ValueError('epsilon must be between 0 and 1')
        self.n_actions = n_actions
        self.lr = lr
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.q_table: Dict[Tuple[int, int], float] = {}

    def choose_action(self, state_hash: int, possible_moves: List[int]) -> int:
        """Selects an action using the agent's internal epsilon-greedy policy. If a random number is less than the current internal epsilon, chooses uniformly among available moves (exploration). Otherwise, chooses the move with the highest Q-value for the given state_hash; ties are broken randomly among the available moves (exploitation). If a state/action pair is not yet in the sparse Q-table, its value is treated as 0. After selecting the action, internal epsilon is multiplied by self.epsilon_decay to facilitate decaying exploration over time. Args: state_hash - The integer identifier of the current state. possible_moves - A list of integers representing valid actions in this state. Returns: The selected action as an integer."""
        if not possible_moves:
            raise ValueError('possible_moves cannot be empty')
        for move in possible_moves:
            if not isinstance(move, int):
                raise ValueError(f'All items in possible_moves must be integers, got {type(move)}')
        for move in possible_moves:
            if move < 0 or move >= self.n_actions:
                raise ValueError(f'Move {move} is out of valid range [0, {self.n_actions})')
        if np.random.rand() < self.epsilon:
            action = int(np.random.choice(possible_moves))
        else:
            q_values = []
            for move in possible_moves:
                q_values.append(self.q_table.get((state_hash, move), 0.0))
            max_q = max(q_values)
            best_moves = [move for move, q in zip(possible_moves, q_values) if q == max_q]
            action = int(np.random.choice(best_moves))
        self.epsilon *= self.epsilon_decay
        return action

    def update(self, state_hash: int, action: int, reward: float, next_state_hash: int, done: bool) -> None:
        """Updates the Q-table entry for the given state and action using the Bellman equation with the agent's internal hyperparameters (lr, gamma). The update rule is: Q(s,a) <- Q(s,a) + lr * (reward + gamma * max(Q(next_s, a')) - Q(s,a)). If 'done' is True, the future value term (gamma * max(Q(next_s))) is zeroed. Missing entries in the sparse Q-table are initialized to 0.0 before the update. Args: state_hash - The integer identifier of the current state. action - The integer action taken. reward - The immediate reward received. next_state_hash - The integer identifier of the next state. done - Boolean indicating if the episode has terminated."""
        current_q = self.q_table.get((state_hash, action), 0.0)
        if done:
            max_future_q = 0.0
        else:
            max_future_q = -np.inf
            for a in range(self.n_actions):
                q_val = self.q_table.get((next_state_hash, a), 0.0)
                if q_val > max_future_q:
                    max_future_q = q_val
            if max_future_q == -np.inf:
                max_future_q = 0.0
        new_q = current_q + self.lr * (reward + self.gamma * max_future_q - current_q)
        self.q_table[state_hash, action] = new_q

    def save_q_table(self, filepath: str) -> None:
        """Saves the Q-table to a binary file (.npy) after converting the sparse dictionary structure into a compatible format (e.g., list of tuples). Args: filepath - The path where the file will be saved."""
        if not self.q_table:
            data = np.array([])
        else:
            states = np.array(list(self.q_table.keys()))
            values = np.array(list(self.q_table.values()))
            data = (states, values)
        with open(filepath, 'wb') as f:
            np.save(f, data)

    def load_q_table(self, filepath: str) -> None:
        """Loads a Q-table from a binary file (.npy) into the agent's q_table attribute (as a dictionary). Overwrites existing values. Args: filepath - The path to the file to load."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f'Q-table file not found: {filepath}')
        with open(filepath, 'rb') as f:
            data = np.load(f, allow_pickle=True)
        self.q_table = {}
        if isinstance(data, dict):
            for state, value in data.items():
                self.q_table[int(state[0]), int(state[1])] = float(value)
        elif hasattr(data, 'size') and data.size > 0:
            states, values = data
            for state, value in zip(states, values):
                self.q_table[int(state[0]), int(state[1])] = float(value)
