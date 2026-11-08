"""
Configuration constants for Tic-Tac-Toe Q-Learning agent.

This module defines hyperparameters required for the training process,
amplifying modularity and reproducibility as per standard academic software practices.

Constants:
    ALPHA (float): Learning rate for the Q-value update rule.
    GAMMA (float): Discount factor for future rewards.
    EPSILON (float): Exploration rate (epsilon-greedy strategy).
    EPISODES (int): Total number of training episodes to execute.
"""

ALPHA: float = 0.2
GAMMA: float = 0.95
EPSILON: float = 0.1
EPISODES: int = 500