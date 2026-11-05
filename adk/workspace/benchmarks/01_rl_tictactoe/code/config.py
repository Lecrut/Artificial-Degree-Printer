import sys
import typing
from collections import defaultdict as _defaultdict

# Hyperparameters for Q-Learning Agent in Tic-Tac-Toe
ALPHA: float = 0.2       # Learning rate (step size)
GAMMA: float = 0.95      # Discount factor
EPSILON: float = 0.1     # Exploration rate
EPISODES: int = 500      # Total training episodes
