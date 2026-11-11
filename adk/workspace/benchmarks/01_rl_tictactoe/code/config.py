"""
Tic-Tac-Toe Q-Learning Configuration Module.

This module defines all hyperparameters and constant settings required for
the reinforcement learning agent's training process.

Constants:
    ALPHA (float): Learning rate for the Q-table updates.
    GAMMA (float): Discount factor for future rewards.
    EPSILON (float): Initial exploration probability.
    EPISODES (int): Total number of training episodes to simulate.
"""
from typing import Final

# Hyperparameters for Q-Learning
ALPHA: Final[float] = 0.2
GAMMA: Final[float] = 0.95
EPSILON: Final[float] = 0.1
EPISODES: Final[int] = 500