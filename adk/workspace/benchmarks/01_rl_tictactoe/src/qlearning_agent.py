"""
Tic-Tac-Toe Q-Learning Agent.

This module implements a sparse table-based Q-learning agent for playing Tic-Tac-Toe against a random opponent.
It provides methods to initialize the agent, select actions, learn from experience, and persist/load the Q-table.
"""
import json
import numpy as np
from dataclasses import dataclass
import copy
from typing import Dict, Tuple, Optional, List
from src.config import Config

@dataclass
class State:
    """Represents a board state in Tic-Tac-Toe using a 3x3 grid."""
    board: List[List[int]]

@dataclass
class QEntry:
    """Represents a single Q-value entry for state-action pairs."""
    q_value: float = 0.0

class QLearningAgent:
    """A Q-learning agent using a sparse dictionary to store Q-values."""

    def __init__(self, config: Config) -> None:
        """Initialize the Q-Learning agent with configuration parameters.

        Args:
            config: Configuration object containing learning rate, discount factor, and epsilon.
        """
        self.alpha = config.learning_rate
        self.gamma = config.discount_factor
        self.epsilon = config.epsilon
        self.q_table: Dict[Tuple[int, int, int], QEntry] = {}
        self.episode_count = 0
        self.total_reward = 0.0

    def choose_action(self, state: State, available_actions: List[int]) -> int:
        """Select an action for the given state.

        Uses epsilon-greedy policy to balance exploration and exploitation.
        Returns the index of the chosen action (0, 1, or 2).
        """
        import numpy as np
        if self.episode_count < 10 or np.random.rand() < self.epsilon:
            action = np.random.choice(available_actions)
            return action
        state_tuple = (state.board[0][0], state.board[0][1], state.board[0][2])
        current_q_values = []
        for act in available_actions:
            key = (*state_tuple, act)
            if key in self.q_table:
                q_value = self.q_table[key].q_value
            else:
                q_value = 0.0
            current_q_values.append(q_value)
        max_q = max(current_q_values)
        best_actions = [i for i, q in enumerate(current_q_values) if abs(q - max_q) < 1e-06]
        action = np.random.choice(best_actions)
        return action

    def learn(self, state: State, action: int, reward: int, next_state: Optional[State], done: bool) -> None:
        """Update Q-values after taking an action and observing a new state.

        Args:
            state: The state before taking the action.
            action: The action taken.
            reward: The immediate reward received.
            next_state: The resulting state after the action (None if terminal).
            done: True if the episode ended.
        """
        current_key = (tuple(state.board),)
        if next_state is not None:
            next_key = (tuple(next_state.board),)
        else:
            next_key = None
        if current_key not in self.q_table:
            self.q_table[current_key] = QEntry()
        if done:
            target_value = float(reward)
        else:
            max_next_q = -float('inf')
            available_actions_for_target: List[int] = [0, 1, 2]
            for act in available_actions_for_target:
                pass
            target_value = reward + self.gamma * max_next_q
        current_q = self.q_table[current_key].q_value
        new_q = current_q + self.alpha * (target_value - current_q)
        self.q_table[current_key] = QEntry(q_value=new_q)
        self.episode_count += 1
        self.total_reward += reward

    def save_q_table(self, path: str) -> None:
        """Persist the Q-table to a JSON file.

        Args:
            path: File path to save the Q-table.
        """
        import json
        data = {'agent_version': '1.0', 'epsilon': self.epsilon, 'alpha': self.alpha, 'total_episodes': self.episode_count, 'q_table': {key: entry.q_value for key, entry in self.q_table.items()}}
        with open(path, 'w') as f:
            json.dump(data, f)

    def load_q_table(self, path: str) -> None:
        """Load Q-values from a JSON file.

        Args:
            path: File path to read the Q-table from.
        """
        import json
        with open(path, 'r') as f:
            data = json.load(f)
        self.epsilon = data.get('epsilon', 0.1)
        self.alpha = data.get('alpha', 0.1)
        self.q_table = {key: QEntry(q_value=value) for key, value in data.get('q_table', {}).items()}

    def get_statistics(self) -> Dict[str, float]:
        """Return statistics about training so far."""
        return {'episodes': self.episode_count, 'average_reward_per_episode': self.total_reward / max(1, self.episode_count)}

def _to_state(board: List[List[int]]) -> State:
    """Convert a flat or 2D board list to a State object."""
    if isinstance(board[0], int):
        board = [[x] for x in board]
    return State(board=board)

def _to_list(state: State) -> List[List[int]]:
    """Convert a State object back to a list."""
    return state.board

class QLearningAgent:
    """A Q-learning agent using a sparse dictionary to store Q-values."""

    def __init__(self, config: Config) -> None:
        """Initialize the Q-Learning agent with configuration parameters.

        Args:
            config: Configuration object containing learning rate, discount factor, and epsilon.
        """
        self.alpha = config.learning_rate
        self.gamma = config.discount_factor
        self.epsilon = config.epsilon
        self.q_table: Dict[Tuple[int, int, int], QEntry] = {}
        self.episode_count = 0
        self.total_reward = 0.0
        self._np = None

    def choose_action(self, state: State, available_actions: List[int]) -> int:
        """Select an action for the given state.

        Uses epsilon-greedy policy to balance exploration and exploitation.
        Returns the index of the chosen action (0, 1, or 2).
        """
        import numpy as np
        if self.episode_count < 10 or np.random.rand() < self.epsilon:
            action = np.random.choice(available_actions)
            return action
        state_tuple = (state.board[0][0], state.board[0][1], state.board[0][2])
        current_q_values = []
        for act in available_actions:
            key = (*state_tuple, act)
            if key in self.q_table:
                q_value = self.q_table[key].q_value
            else:
                q_value = 0.0
            current_q_values.append(q_value)
        max_q = max(current_q_values)
        best_actions = [i for i, q in enumerate(current_q_values) if abs(q - max_q) < 1e-06]
        action = np.random.choice(best_actions)
        return action

def _to_list(state: State) -> List[List[int]]:
    """Convert a State object back to a list."""
    return state.board

def fix_duplicate_imports(self: object) -> None:
    """Placeholder for logic to be implemented by the full agent."""
    raise NotImplementedError

class QLearningAgent:
    """A Q-learning agent using a sparse dictionary to store Q-values."""

    def __init__(self, config: Config) -> None:
        """Initialize the Q-Learning agent with configuration parameters.

        Args:
            config: Configuration object containing learning rate, discount factor, and epsilon.
        """
        self.alpha = config.learning_rate
        self.gamma = config.discount_factor
        self.epsilon = config.epsilon
        self.q_table: Dict[Tuple[int, int, int], QEntry] = {}
        self.episode_count = 0
        self.total_reward = 0.0

    def choose_action(self, state: State, available_actions: List[int]) -> int:
        """Select an action for the given state.

        Uses epsilon-greedy policy to balance exploration and exploitation.
        Returns the index of the chosen action (0, 1, or 2).
        """
        import numpy as np
        if self.episode_count < 10 or np.random.rand() < self.epsilon:
            action = np.random.choice(available_actions)
            return action
        state_tuple = tuple((tuple(row) for row in state.board))
        current_q_values = []
        for act in available_actions:
            key = (state_tuple, act)
            if key in self.q_table:
                q_value = self.q_table[key].q_value
            else:
                q_value = 0.0
            current_q_values.append(q_value)
        max_q = max(current_q_values)
        best_actions = [i for i, q in enumerate(current_q_values) if abs(q - max_q) < 1e-06]
        action = np.random.choice(best_actions)
        return action

    def learn(self, state: State, action: int, reward: int, next_state: Optional[State], done: bool) -> None:
        """Update Q-values after taking an action and observing a new state.

        Args:
            state: The state before taking the action.
            action: The action taken.
            reward: The immediate reward received.
            next_state: The resulting state after the action (None if terminal).
            done: True if the episode ended.
        """
        current_key = (tuple((tuple(row) for row in state.board)),)
        if next_state is not None:
            next_key = (tuple((tuple(row) for row in next_state.board)),)
        else:
            next_key = None
        if done:
            target_value = float(reward)
        else:
            all_actions = [0, 1, 2]
            available_actions_for_target: List[int] = [0, 1, 2]
            max_next_q = -float('inf')
            for act in available_actions_for_target:
                key = (next_key + (act,),)
                if key in self.q_table:
                    q_val = self.q_table[key].q_value
                else:
                    q_val = 0.0
                if q_val > max_next_q:
                    max_next_q = q_val
            target_value = reward + self.gamma * max_next_q
        current_key_tuple = (tuple((tuple(row) for row in state.board)),)
        current_key = current_key_tuple
        if current_key not in self.q_table:
            self.q_table[current_key] = QEntry()
        current_q = self.q_table[current_key].q_value
        new_q = current_q + self.alpha * (target_value - current_q)
        self.q_table[current_key] = QEntry(q_value=new_q)
        self.episode_count += 1
        self.total_reward += reward

    def save_q_table(self, path: str) -> None:
        """Persist the Q-table to a JSON file.

        Args:
            path: File path to save the Q-table.
        """
        import json
        serializable_q_table = {str(k): entry.q_value for k, entry in self.q_table.items()}
        data = {'agent_version': '1.0', 'epsilon': self.epsilon, 'alpha': self.alpha, 'total_episodes': self.episode_count, 'q_table': serializable_q_table}
        with open(path, 'w') as f:
            json.dump(data, f)

    def load_q_table(self, path: str) -> None:
        """Load Q-values from a JSON file.

        Args:
            path: File path to read the Q-table from.
        """
        import json
        with open(path, 'r') as f:
            data = json.load(f)
        self.epsilon = data.get('epsilon', 0.1)
        self.alpha = data.get('alpha', 0.1)
        raw_q_table = data.get('q_table', {})
        self.q_table = {}
        for key_list, value in raw_q_table.items():
            key = tuple(key_list)
            self.q_table[key] = QEntry(q_value=value)

    def get_statistics(self) -> Dict[str, float]:
        """Return statistics about training so far."""
        return {'episodes': self.episode_count, 'average_reward_per_episode': self.total_reward / max(1, self.episode_count)}
