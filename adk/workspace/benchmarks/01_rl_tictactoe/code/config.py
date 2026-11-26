"""Defines all hyperparameters, experiment settings, and constants used for the Q-Learning Tic-Tac-Toe project."""
NUM_EPISODES: int = 2000
TEST_EPISODES: int = 100
SEEDS: list[int] = [42, 1337]
LEARNING_RATE: float = 0.1
GAMMA: float = 0.9
EPSILON_START: float = 1.0
EPSILON_END: float = 0.01
EPSILON_DECAY: float = 0.995
