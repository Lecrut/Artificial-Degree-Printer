"""Konfiguracja parametrow eksperymentu Q-Learning dla Tic-Tac-Toe."""
import os
from typing import List
from dataclasses import dataclass
LEARNING_RATE: float = 0.1
DISCOUNT_FACTOR: float = 0.95
EPSILON_START: float = 1.0
EPSILON_END: float = 0.05
EPSILON_DECAY: float = 0.95
MAX_EPISODES: int = 10000
NUM_EVAL_GAMES: int = 5000
TRAIN_SEED: int = 42
EVAL_SEED: int = 42

@dataclass
class ResultsConfig:
    """Configuration for saving experiment results."""
    output_path: str
    metrics: List[str]

    def __post_init__(self):
        """Set default metrics if not provided."""
        if self.metrics == []:
            self.metrics = ['win_rate', 'avg_reward']

def get_results_dir() -> str:
    """Returns the directory path for saving experiment results."""
    return '.'
