"""Training loop for Q-Learning agent against a random baseline."""
from __future__ import annotations
import time
from typing import Any, cast
import numpy as np

class Config:
    """Hyperparameters for the training experiment."""
    ENV_SEED: int = 42
    AGENT_SEED: int = 123
    RANDOM_BASELINE_SEED: int = 456
    NUM_EPISODES: int = 1000
    EVAL_EVERY_N_EPISODES: int = 50
    MAX_STEPS: int = 9
    GAMMA: float = 0.95

    def __init__(self, env_seed: int=42, agent_seed: int=123, random_baseline_seed: int=456, num_episodes: int=1000, eval_every_n_episodes: int=50, max_steps: int=9, gamma: float=0.95) -> None:
        self.env_seed = env_seed
        self.agent_seed = agent_seed
        self.random_baseline_seed = random_baseline_seed
        self.num_episodes = num_episodes
        self.eval_every_n_episodes = eval_every_n_episodes
        self.max_steps = max_steps
        self.gamma = gamma

class TrainingResults:
    """Container for metrics collected during training."""

    def __init__(self) -> None:
        self.episode_rewards: list[float] = []
        self.episode_win_rates: list[float] = []
        self.episode_draw_rates: list[float] = []
        self.convergence_epoch: int | None = None

def train(qlearning_agent: Any, random_baseline_env: Any, config: Config, env: Any) -> TrainingResults:
    """Execute the training loop to collect metrics.

Returns a TrainingResults object populated with episode-level statistics
and convergence flags.
"""
    results = TrainingResults()
    np.random.seed(config.env_seed)
    for episode in range(config.num_episodes):
        state_ql = env.reset(seed=config.env_seed)
        state_base = random_baseline_env.reset()
        total_reward = 0.0
        wins_in_episode = 0
        draws_in_episode = 0
        step = 0
        done = False
        while not done:
            if qlearning_agent.total_rewards is None:
                qlearning_agent.total_rewards = []
            qlearning_agent.total_rewards.append(0.0)
            action_ql = np.random.randint(2)
            reward, done, state_ql = qlearning_agent.step(state_ql, action=action_ql)
            total_reward += reward
            qlearning_agent.total_rewards[-1] = reward
            action_base = np.random.randint(2)
            _, done, state_base = random_baseline_env.step(action=action_base)
            step += 1
        results.episode_rewards.append(total_reward)
        if total_reward > 0:
            wins_in_episode += 1
        else:
            draws_in_episode += 1
        episode_len = len(qlearning_agent.total_rewards)
        current_win_rate = wins_in_episode / max(episode_len, 1)
        results.episode_win_rates.append(current_win_rate)
        if total_reward <= 0:
            pass
        else:
            draws_in_episode += 1
            current_draw_rate = draws_in_episode / max(episode_len, 1)
            results.episode_draw_rates.append(current_draw_rate)
        if episode % config.eval_every_n_episodes == 0 or episode == config.num_episodes - 1:
            pass
        results.convergence_epoch = episode + 1
    return results
