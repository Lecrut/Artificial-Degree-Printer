"""Module owning the interaction loop between the Tic-Tac-Toe environment and the Q-Learning agent, providing utilities to run single episodes (instantiating internal components) and full training sessions."""
import numpy as np
from typing import Callable, Dict, Tuple
from environment import TicTacToeEnv
from q_agent import QAgent
from baseline_agent import RandomAgent

def run_episode(env_class: type, agent_class: type, epsilon: float, lr: float, gamma: float) -> Tuple[float, int]:
    """Runs a single episode of Tic-Tac-Toe between the Q-Learning agent and a Random Agent opponent.

    Instantiates `TicTacToeEnv`, `QAgent` (played as Player X), and `RandomAgent` (played as Player O). The environment alternates turns. The Q-Agent updates its table after each step using the provided learning rate (`lr`) and discount factor (`gamma`).

    Args:
        env_class: The class for the Tic-Tac-Toe environment.
        agent_class: The class for the Q-Learning agent.
        epsilon: The exploration probability used by the agent at the start of the episode.
        lr: The learning rate for Q-learning updates.
        gamma: The discount factor for future rewards.

    Returns:
        tuple: A tuple containing:
            - total_reward (float): The sum of rewards received by the agent during the episode.
            - num_steps (int): The number of steps taken in the episode before termination."""
    raise NotImplementedError

def train_policy(n_episodes: int, env_params: Dict[str, any], agent_params: Dict[str, any], epsilon_decay_fn: Callable[[int], float]) -> Dict[str, any]:
    """Trains the Q-Agent over a specified number of episodes against a Random Agent opponent.

    Instantiates `TicTacToeEnv` and `QAgent` using the provided parameters. Creates a `RandomAgent` instance for the opponent. Iteratively calls `run_episode` for `n_episodes`. Adjusts the exploration parameter `epsilon` after each episode using `epsilon_decay_fn`. Aggregates metrics such as average reward per 100 episodes and final epsilon value.

    Args:
        n_episodes: Total number of training episodes.
        env_params: Dictionary of parameters to pass to the environment constructor (typically empty for TicTacToeEnv).
        agent_params: Dictionary containing 'n_states' and 'n_actions' for the QAgent constructor.
        epsilon_decay_fn: A function that takes the current episode index (0-indexed) and returns the new epsilon value.

    Returns:
        dict: Training statistics including:
            - 'trained_agent': The trained agent instance with its final Q-table.
            - 'avg_rewards': List of average rewards calculated every 10 episodes.
            - 'final_epsilon': The value of epsilon after the last episode."""
    raise NotImplementedError
