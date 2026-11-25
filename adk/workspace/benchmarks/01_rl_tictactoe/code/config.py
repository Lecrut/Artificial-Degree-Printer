"""Defines all experiment hyperparameters and run settings as module-level constants."""
import numpy as np
N_EPISODES: int = 500
N_TEST_GAMES: int = 200
N_RUNS: int = 3
SEED_BASE: int = 42
LEARNING_RATE: float = 0.1
GAMMA: float = 0.9
EPSILON_DECAY: float = 0.995
EPSILON_MIN: float = 0.01
