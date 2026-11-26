"""Implements Tic-Tac-Toe game logic as a Gymnasium-compatible environment and provides utilities for episode simulation."""
import gymnasium as gym
import numpy as np
from typing import Any, Dict, List, Optional, Tuple

class TicTacToeEnv(gym.Env):
    """A Gymnasium environment for the Tic-Tac-Toe game, using a flat action space and 3x3 grid observation."""
    action_space: gym.spaces.Discrete
    observation_space: gym.spaces.Box

    def __init__(self) -> None:
        """Initializes the Tic-Tac-Toe environment. Sets up action and observation spaces."""
        self.board: np.ndarray = np.zeros((3, 3), dtype=int)
        self.action_space: gym.spaces.Discrete = gym.spaces.Discrete(9)
        self.observation_space: gym.spaces.Box = gym.spaces.Box(low=-1, high=1, shape=(3, 3), dtype=np.int8)

    def reset(self, seed: Optional[int]=None) -> tuple[np.ndarray, dict]:
        """Resets the environment to the initial state (empty board). Returns the initial observation and an info dictionary."""
        super().reset(seed=seed)
        self.board = np.zeros((3, 3), dtype=int)
        return (self._flatten_observation(), {'state': 'start', 'turn': 'X'})

    def step(self, action: int) -> tuple[np.ndarray, float, bool, bool, dict]:
        """Takes a step in the environment. Returns obs, reward, done, trunc, info."""
        if self.board.flat[action] != 0:
            raise ValueError(f'Invalid action {action} for board state.')
        player = 'X' if np.all(self.board == 0) else 'O'
        row, col = divmod(action, 3)
        self.board[row, col] = 1 if player == 'X' else -1
        done = False
        trunc = False
        reward = 0
        info = {'turn': 'X' if np.all(self.board == 0) else 'O', 'winner': None}
        winner = self._get_winner(self.board)
        if winner:
            done = True
            trunc = True
            reward = 1 if player == winner else -1
            info['winner'] = winner
        elif not np.any(np.all(self.board != 0), axis=None):
            done = True
            trunc = True
            reward = 0
        return (self._flatten_observation(), float(reward), done, trunc, info)

    def get_valid_actions(self, obs: np.ndarray) -> list[int]:
        """Returns a list of valid action indices for the given observation."""
        flattened_obs = obs.flatten()
        return [i for i in range(9) if flattened_obs[i] == 0]

    def _get_winner(self, board: np.ndarray) -> Optional[str]:
        """Determines the winner of the game based on the current board state."""
        flat = board.flatten()
        win_cases = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
        for r, c, d in win_cases:
            if flat[r] != 0 and flat[r] == flat[c] and (flat[r] == flat[d]):
                return 'X' if flat[r] == 1 else 'O'
        return None

    def _flatten_observation(self) -> np.ndarray:
        """Helper to get observation as a 1D array."""
        return self.board.flatten().astype(np.int8)

def run_episode(env: gym.Env, agent_p1: Any, agent_p2: Any, player_turn: str='X') -> dict:
    """Simulates a complete episode of Tic-Tac-Toe. Returns info and turns."""
    obs, info = env.reset()
    state_history = [obs.copy(), {'state': 'start', 'turn': player_turn}]
    while not info['done']:
        valid_actions = env.get_valid_actions(obs)
        if len(valid_actions) == 0:
            break
        current_player = info['turn']
        action_taken = None
        if current_player == 'X':
            try:
                action_taken = agent_p1(obs, valid_actions)
            except Exception:
                action_taken = valid_actions[0] if valid_actions else 0
        else:
            try:
                action_taken = agent_p2(obs, valid_actions)
            except Exception:
                action_taken = valid_actions[0] if valid_actions else 0
        if action_taken is None:
            break
        obs_new, reward, done, trunc, info = env.step(action_taken)
        state_history.append((obs.copy(), action_taken))
    return {'info': info, 'turns': state_history}

def parse_episode_result(info: dict, p1_id: str, p2_id: str) -> dict:
    """Parses the final step info to determine game outcome."""
    winner = info.get('winner', None)
    result = 'win' if winner == p1_id else 'loss' if winner == p2_id else 'draw'
    rewards = {p1_id: 1 if result == 'win' else -1 if result == 'loss' else 0, p2_id: -1 if result == 'win' else 1 if result == 'loss' else 0}
    return {'winner': winner, 'result': result, 'rewards': rewards}
