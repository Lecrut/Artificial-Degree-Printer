"""Configuration module for Tic-Tac-Toe Q-Learning experiment."""
import numpy as np

# --- Experiment Meta-parameters (Global Constants) ---
N_RUNS: int = 5
RANDOM_SEED: int = 42
EPOCHES_PER_EVALUATION: int = 1000
AGENT_WIN_RATE_THRESHOLD: float = 0.6
BASELINE_WIN_RATE_TARGET: float = 0.33


class Config:
    """Academic experiment configuration."""

    def __init__(self) -> None:
        """Initialize with hardcoded hyperparameters as instance attributes."""
        self.learning_rate: float = 0.1
        self.discount_factor: float = 0.95
        self.epsilon_start: float = 1.0
        self.epsilon_end: float = 0.01
        self.epsilon_decay: float = 0.995
        self.total_episodes: int = 50000
        self.seed: int = RANDOM_SEED

    def to_dict(self) -> dict:
        """Return configuration as a dictionary for CSV compatibility."""
        return {
            'learning_rate': self.learning_rate,
            'discount_factor': self.discount_factor,
            'epsilon_start': self.epsilon_start,
            'epsilon_end': self.epsilon_end,
            'epsilon_decay': self.epsilon_decay,
            'total_episodes': self.total_episodes,
            'seed': self.seed
        }
