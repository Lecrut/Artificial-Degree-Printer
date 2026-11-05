"""
Hyperparameter configuration for the Q-Learning Tic-Tac-Toe agent.

This module centralizes all numerical constants and training hyperparameters
to ensure reproducibility and easy tuning across the thesis evaluation framework.

Types:
    ALPHA: Float representing the learning rate (\\alpha).
    GAMMA: Float representing the discount factor (\\gamma).
    EPSILON: Float representing the exploration rate (\\epsilon).
    EPISODES: Integer representing the total number of training episodes.
"""

from typing import Final

# Learning rate \\alpha
ALPHA: Final[float] = 0.2

# Discount factor \\gamma
GAMMA: Final[float] = 0.95

# Exploration rate \\epsilon
EPSILON: Final[float] = 0.1

# Total training episodes
EPISODES: Final[int] = 500