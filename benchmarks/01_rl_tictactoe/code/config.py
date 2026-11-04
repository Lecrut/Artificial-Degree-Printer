"""
Tic-Tac-Toe Q-Learning Configuration Module.

This module defines all hyperparameters and environment constants used for the
reinforcement learning agent (tabular Q-Learning) described in the thesis.

Constants:
    ALPHA (float): Learning rate (\alpha). Controls how much new information overrides old information.
    GAMMA (float): Discount factor (\gamma). Determines the importance of future rewards.
    EPSILON (float): Exploration rate. Probability of choosing a random action over the optimal one.
    EPISODES (int): Total number of training episodes.
"""

# --- Hyperparameters ---
ALPHA: float = 0.2
GAMMA: float = 0.95
EPSILON: float = 0.1
EPISODES: int = 500