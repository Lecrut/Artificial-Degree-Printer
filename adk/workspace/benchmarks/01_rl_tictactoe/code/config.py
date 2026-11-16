"""Hyperparameter and configuration constants for the Tic-Tac-Toe Q-Learning experiment.

This module declares all fixed settings used by run_experiments. Every function reads from here,
never relying on default literals, ensuring reproducibility and testability.

Symbols:
- RANDOM_SEED: Integer random seed.
- N_EPISODES_PER_RUN: Number of episodes per single run of an agent against a random opponent.
- N_REPETITIONS: Total number of independent experiments (random seeds x runs).
- EPSILON_START, EPSILON_END, DECAY_RATE: Parameters for epsilon decay schedule.
- ALPHA, GAMMA: Learning rate and discount factor for Q-Learning.
- EPOCHES_PER_DECAY_STEP: Frequency at which epsilon is decayed.
- METRICS_TO_REPORT: List of metric names to include in the results CSV.
- OUTPUT_CSV: Filename for the results output file.
"""
RANDOM_SEED: int = 42
N_EPISODES_PER_RUN: int = 100
N_REPETITIONS: int = 3
EPSILON_START: float = 1.0
EPSILON_END: float = 0.05
DECAY_RATE: float = 0.99
ALPHA: float = 0.1
GAMMA: float = 0.9
EPOCHES_PER_DECAY_STEP: int = N_EPISODES_PER_RUN // 2
METRICS_TO_REPORT: list[str] = ['win_rate_agent', 'draw_rate', 'loss_rate_agent', 'average_reward_per_episode']
OUTPUT_CSV: str = 'results.csv'
OUTPUT_CSV: str = 'results.csv'
OUTPUT_CSV: str = 'results.csv'
