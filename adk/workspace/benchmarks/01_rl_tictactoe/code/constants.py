"""Defines global constants for file paths, experiment hyperparameters (lr, gamma, epsilon, episodes), and seeds to ensure reproducibility."""
import os
from typing import Final
RESULTS_CSV_PATH: Final[str] = 'results.csv'
TRAIN_LOG_CSV_PATH: Final[str] = 'train_log.csv'
FIGURES_DIR: Final[str] = 'figures'
EPISODES: Final[int] = 5000
N_RUNS: Final[int] = 3
LEARNING_RATE: Final[float] = 0.1
DISCOUNT_FACTOR: Final[float] = 0.99
EXPLORATION_RATE: Final[float] = 0.1
