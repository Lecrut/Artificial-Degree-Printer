"""Implementacja agenta Q-Learning do gry w Tic-Tac-Toe."""
from typing import Dict, List, Tuple
import random

class QLearningAgent:
    """Agent uczący się poprzez Q-Learning z epsilon-greedy polityką."""
    lr: float
    gamma: float
    epsilon: float
    epsilon_end: float
    epsilon_decay: float
    q_table: Dict[Tuple[int, ...], List[float]]

    def __init__(self, learning_rate: float=0.1, discount_factor: float=0.95, epsilon_start: float=0.8, epsilon_end: float=0.05, epsilon_decay: float=0.995) -> None:
        """Inicjalizuje agenta z podanymi hiperparametrami.

Args:
    learning_rate (float): Learning rate for Q-values update.
    discount_factor (float): Discount factor for future rewards.
    epsilon_start (float): Initial exploration rate.
    epsilon_end (float): Final minimum exploration rate.
    epsilon_decay (float): Decay rate for exploration schedule.

"""
        self.lr: float = learning_rate
        self.gamma: float = discount_factor
        self.epsilon: float = epsilon_start
        self.epsilon_end: float = epsilon_end
        self.epsilon_decay: float = epsilon_decay
        self.q_table: Dict[Tuple[int, ...], List[float]] = {}

    def reset(self) -> None:
        """Resets the exploration rate to start value for new training sessions."""
        self.epsilon: float = self.epsilon_start

    def get_q_values(self, state: List[int]) -> List[float]:
        """Returns Q-values for all possible actions in the given state. Returns zeros if state unseen."""
        key: Tuple[int, ...] = self._state_to_key(state)
        q_values: List[float] = self.q_table.get(key, [0.0] * 9)
        return q_values

    def choose_action(self, state: List[int], valid_moves: List[int]) -> int:
        """Chooses an action using epsilon-greedy policy based on valid moves.

Args:
    state (List[int]): Current game state.
    valid_moves (List[int]): Indices of available actions.

Returns:
    Index of the selected action from valid_moves.
"""
        if not valid_moves:
            raise ValueError('No valid moves available in the current state.')
        if random.uniform(0, 1) < self.epsilon:
            return random.choice(valid_moves)
        max_q = float('-inf')
        best_actions: List[int] = []
        for action_idx in valid_moves:
            state_key: Tuple[int, ...] = self._state_to_key(state)
            current_q_list: List[float] = self.q_table.get(state_key, [0.0] * 9)
            q_val: float = current_q_list[action_idx]
            if q_val > max_q:
                max_q = q_val
                best_actions = [action_idx]
            elif abs(q_val - max_q) < 1e-06:
                best_actions.append(action_idx)
        if not best_actions:
            best_actions = valid_moves
        return random.choice(best_actions)

    def update(self, state: List[int], action: int, reward: float, next_state: List[int]) -> None:
        """Updates the Q-value for the given state-action pair.

    Args:
        state (List[int]): Current game state.
        action (int): Index of the action taken in the current state.
        reward (float): Reward received after taking the action.
        next_state (List[int]): Resulting game state after the action.
    """
        row: int = action // 3
        col: int = action % 3
        key: Tuple[int, ...] = self._state_to_key(state)
        if key not in self.q_table:
            self.q_table[key]: List[float] = [0.0] * 9
        q_values: List[float] = self.q_table[key]
        next_key: Tuple[int, ...] = self._state_to_key(next_state)
        if next_key not in self.q_table:
            self.q_table[next_key]: List[float] = [0.0] * 9
        next_q_values: List[float] = self.q_table[next_key]
        current_q: float = q_values[action]
        td_target: float = reward + self.gamma * max(next_q_values) if next_q_values else 0.0
        delta: float = td_target - current_q
        act_idx: int = action
        if act_idx < len(q_values):
            q_values[act_idx] += self.lr * delta

    def decay_epsilon(self) -> None:
        """Decreases epsilon towards epsilon_end."""
        self.epsilon: float = max(self.epsilon * self.epsilon_decay, self.epsilon_end)

    def _state_to_key(self, state: List[int]) -> Tuple[int, ...]:
        """Converts state list to tuple key for dictionary lookup."""
        return tuple(state)
