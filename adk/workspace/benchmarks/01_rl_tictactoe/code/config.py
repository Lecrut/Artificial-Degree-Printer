"""Defines all experiment hyperparameters and constants as module-level variables for reproducibility."""
import numpy as np
from typing import Final

# Training Configuration
TRAIN_EPISODES: Final[int] = 50000
EVAL_EPISODES: Final[int] = 1000

# Reinforcement Learning Parameters
LEARNING_RATE: Final[float] = 0.1
DISCOUNT_FACTOR: Final[float] = 0.95
INITIAL_EPSILON: Final[float] = 1.0
FINAL_EPSILON: Final[float] = 0.01
DECAY_RATE: Final[float] = 0.99995
SEED: Final[int] = 42
