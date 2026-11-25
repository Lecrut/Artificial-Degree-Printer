"""Implements the Tabular Q-Learning algorithm and state representation logic."""
from typing import Dict
import numpy as np
from environment import TicTacToeEnv
BOARD_DIM: int = 3
TOTAL_CELLS: int = 9

def encode_state(board: np.ndarray) -> str:
    """Encode a Tic-Tac-Toe board into a unique string key.

    Converts the flat NumPy array (shape (9,), values in {0, 1, 2}) into 
    a string representation suitable for use as a dictionary key in the Q-table.
    The encoding is canonical: it relies on the exact sequence of cell values.

    Args:
        board: A numpy array of shape (9,) representing the current game state.
               Values must be 0 (empty), 1 (X), or 2 (O).

    Returns:
        key: A string representation of the board, e.g., '000000000' for empty, 
             '100020...' for mixed states. The length is always 9.
    """
    return ''.join((str(val) for val in board.tolist()))

class QLearningAgent:
    """A tabular Q-Learning agent using an epsilon-greedy policy.

    This agent maintains a Q-table (dict) mapping encoded state strings to 
    NumPy arrays of Q-values. It interacts with the TicTacToeEnv environment.

    Attributes:
        q_table: Dict[str, np.ndarray]. A dictionary where keys are encoded 
                 state strings (output of encode_state) and values are numpy 
                 arrays of shape (9,) containing Q-values for each possible action.
                 Initialized to zeros on first access.
        alpha: float. The learning rate.
        gamma: float. The discount factor.
        epsilon: float. The current exploration rate.
    """
    q_table: Dict[str, np.ndarray]
    alpha: float
    gamma: float
    epsilon: float

    def __init__(self, state_size: int, alpha: float, gamma: float, epsilon: float) -> None:
        """Initialize the Q-Learning agent.

    Args:
        state_size: The number of possible actions (9 for Tic-Tac-Toe).
            This parameter is included for compatibility with 
            standard RL interfaces, though it is implicitly 9 here.
        alpha: The learning rate for updating Q-values. Must be in (0, 1].
        gamma: The discount factor for future rewards. Must be in [0, 1].
        epsilon: The initial exploration probability. Must be in (0, 1).
    """
        self.q_table: Dict[str, np.ndarray] = {}
        self.alpha: float = alpha
        self.gamma: float = gamma
        self.epsilon: float = epsilon

    def select_action(self, state: np.ndarray) -> int:
        """Select an action for the given state using the epsilon-greedy policy.

    If a random number is less than epsilon, returns a uniformly random 
    integer in [0, 8]. Otherwise, returns the action with the highest Q-value
    for the current encoded state. If there are ties among maximum Q-values, 
    the smallest action index is chosen.

    Note: This function does not check if the chosen action is legal (i.e., 
    if the cell is empty). It assumes the caller (environment or step logic) 
    handles validity or that illegal moves are handled by zero reward/termination.

    Args:
        state: The current board observation from TicTacToeEnv (np.ndarray of shape (9,)).

    Returns:
        action: An integer in [0, 8] representing the selected cell index.
    """
        if self.epsilon > 0:
            return np.random.randint(0, 9)
        state_key = encode_state(state)
        q_values = self.q_table.get(state_key, np.zeros(9))
        max_q = np.max(q_values)
        best_actions = [i for i in range(9) if q_values[i] == max_q]
        return min(best_actions)

    def update(self, state: np.ndarray, action: int, reward: float, next_state: np.ndarray, done: bool) -> None:
        """Update the Q-value for the given state-action pair.

    Applies the Q-Learning update rule:
    Q(s, a) <- Q(s, a) + alpha * (target - Q(s, a))
    where target = reward + gamma * max_a' Q(s', a') if not done, else reward.

    Args:
        state: The previous environment observation (np.ndarray of shape (9,)).
        action: The integer index of the action taken in 'state'.
        reward: The scalar reward received after taking the action.
        next_state: The new environment observation after the step (np.ndarray of shape (9,)).
        done: Boolean flag indicating if the episode has terminated or truncated.
    """
        state_key = encode_state(state)
        q_current = self.q_table.get(state_key, np.zeros(9))
        old_q = q_current[action]
        if not done:
            next_state_key = encode_state(next_state)
            max_next_q = 0.0
            for a in range(9):
                next_q = self.q_table.get(next_state_key, np.zeros(9))[a]
                max_next_q = max(max_next_q, next_q)
            target = reward + self.gamma * max_next_q
        else:
            target = reward
        self.q_table[state_key] = q_current.copy()
        self.q_table[state_key][action] = old_q + self.alpha * (target - old_q)
