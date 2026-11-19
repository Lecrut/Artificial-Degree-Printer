"""Configuration constants for the Tic-Tac-Toe Q-Learning experiment."""
LEARNING_RATE: float = 0.1
DISCOUNT_FACTOR: float = 0.95
EPSILON_START: float = 1.0
EPSILON_END: float = 0.01
EPSILON_DECAY: float = 0.995
MAX_EPISODES: int = 100000
TEST_EPISODES: int = 1000
SEED: int = 42
OUTPUT_DIR: str = 'results'
