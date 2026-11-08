"""Hyperparameters for the Tic-Tac-Toe Q-Learning Agent.

This module defines constants required by `core.py` for deterministic training
and evaluation of the reinforcement learning agent. All symbols are exported
to support AST pointer resolution in thesis documentation.
"""
from typing import Final

# Learning rate (alpha)
ALPHA: Final[float] = 0.2

# Discount factor (gamma)
GAMMA: Final[float] = 0.95

# Exploration rate (epsilon)
EPSILON: Final[float] = 0.1

# Total number of training episodes
EPISODES: Final[int] = 500

# Sample size for Monte Carlo estimation in baseline/benchmarking
SAMPLE_SIZE: Final[int] = 1000

# Default learning rate for any auxiliary optimizers or fallbacks
LEARNING_RATE: Final[float] = 0.01
