"""Defines hyperparameters, seeds, and repetition counts for the Q-Learning Tic-Tac-Toe experiment to ensure reproducibility."""
LEARNING_RATE: float = 0.15
DISCOUNT_FACTOR: float = 0.9
INITIAL_EPSILON: float = 1.0
FINAL_EPSILON: float = 0.01
EPSILON_DECAY: float = 0.99
TOTAL_EPISODES: int = 50000
TEST_EPISODES: int = 1000
SEED: int = 42
GAMMA: float = 0.9
