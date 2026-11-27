"""Manages the training loop for a Q-Learning agent against a random baseline environment."""
import numpy as np
from typing import Tuple, Dict, Any, List
from environment import TicTacToeEnv
from q_agent import QAgent
DEFAULT_LR: float = 0.1
DEFAULT_GAMMA: float = 0.99
EPSILON_DECAY_RATE: float = 0.995
MIN_EPSILON: float = 0.01

def train_episode(env: TicTacToeEnv, q_agent: QAgent, epsilon: float, seed: int=None) -> Tuple[float, int]:
    """Runs a single episode of Tic-Tac-Toe between the Q-Agent and a Random Agent.

    Args:
        env: The Gymnasium-compatible environment instance, expected to be already reset or reset within this function if state is None.
        q_agent: The Q-Learning agent being trained.
        epsilon: Current exploration rate for the epsilon-greedy policy.
        seed: Optional seed for initializing the internal RandomAgent. If provided, ensures deterministic baseline moves.

    Returns:
        tuple: (total_reward, num_steps)
            - total_reward: Sum of rewards received by the Q-Agent during the episode.
            - num_steps: Number of steps taken until termination.

    Raises:
        ValueError: If an invalid action is selected or if the environment state becomes inconsistent."""
    from baseline_agent import RandomAgent
    obs, _ = env.reset(seed)
    done = False
    truncated = False
    total_reward = 0.0
    step_count = 0
    opponent = RandomAgent(seed) if seed is not None else RandomAgent(None)
    while not (done or truncated):
        moves = env.get_valid_moves()
        action = q_agent.choose_action(env.get_state_hash(env.state), moves)
        next_obs, reward, done, truncated, _ = env.step(action)
        total_reward += reward
        next_state_hash = env.get_state_hash(next_obs) if isinstance(next_obs, np.ndarray) else next_obs
        q_agent.update(env.get_state_hash(obs), action, reward, next_state_hash, done)
        obs = next_obs
        step_count += 1
    return (total_reward, step_count)

def train_policy(n_episodes: int, env_seed: int=None) -> Dict[str, Any]:
    """Trains the Q-Agent for a specified number of episodes against a Random Baseline.

    Args:
        n_episodes: Total number of training episodes to run.
        env_seed: Optional seed for initializing the environment. Ensures reproducibility of game outcomes.

    Returns:
        dict: Training statistics containing:
            - 'rewards' (list[float]): List of total rewards per episode.
            - 'avg_reward_window' (float): Moving average of the last 100 episodes (0.0 if less than 100 episodes).
            - 'final_epsilon' (float): The value of epsilon after training.
            - 'trained_agent' (QAgent): The trained QAgent instance."""
    import random
    from q_agent import QAgent
    from environment import TicTacToeEnv, BOARD_SIZE, NUM_ACTIONS
    from baseline_agent import RandomAgent
    from experiment import INITIAL_EPSILON, FINAL_EPSILON, N_EPISODES, LEARNING_RATE, GAMMA

    def _epsilon_decay_fn(episode: int) -> float:
        """Linearly decays epsilon from INITIAL_EPSILON to FINAL_EPSILON over N_EPISODES. Returns the current epsilon value for the given episode index (0-indexed). If episode >= N_EPISODES, returns FINAL_EPSILON."""
        if episode >= N_EPISODES:
            return FINAL_EPSILON
        progress: float = episode / (N_EPISODES - 1)
        return INITIAL_EPSILON + progress * (FINAL_EPSILON - INITIAL_EPSILON)
    q_agent: QAgent = QAgent(n_actions=NUM_ACTIONS, lr=LEARNING_RATE, gamma=GAMMA, epsilon=INITIAL_EPSILON, epsilon_decay=_epsilon_decay_fn)
    rewards: list[float] = []
    for episode_idx in range(n_episodes):
        env: TicTacToeEnv = TicTacToeEnv()
        env.reset(seed=env_seed + episode_idx if env_seed is not None else None)
        current_epsilon: float = _epsilon_decay_fn(episode_idx)
        done: bool = False
        total_reward: float = 0.0
        while not done:
            state_hash: int = env.get_state_hash(env.board)
            possible_moves: list[int] = env.get_valid_moves()
            action: int = q_agent.choose_action(state_hash, possible_moves)
            next_state_hash, reward, done, _ = env.step(action)
            q_agent.update(state_hash, action, reward, next_state_hash, done)
            total_reward += reward
        rewards.append(total_reward)
    avg_reward_window: float = 0.0
    if len(rewards) >= 100:
        avg_reward_window = sum(rewards[-100:]) / 100.0
    elif len(rewards) > 0:
        avg_reward_window = sum(rewards) / len(rewards)
    return {'rewards': rewards, 'avg_reward_window': avg_reward_window, 'final_epsilon': q_agent.epsilon, 'trained_agent': q_agent}
