"""
Global configuration for the Tic-Tac-Toe Q-Learning experiment.
All parameters are module-level symbols to ensure they can be cited in the thesis.
"""
import numpy as np
TRAINING_EPOCHS: int = 5000
MAX_STEPS_PER_EPISOD: int = 9
N_EPISODES_TO_REPORT: int = 10
ALPHA: float = 0.1
GAMMA: float = 0.95
EPSILON_DECAY_RATE: float = 0.995
EPSILON_MIN: float = 0.01
NUM_EVALUATION_RUNS: int = 20
RANDOM_SEED: int = 42
PLAYER_NINE: int = 9
EPSILON: float = 0.1
