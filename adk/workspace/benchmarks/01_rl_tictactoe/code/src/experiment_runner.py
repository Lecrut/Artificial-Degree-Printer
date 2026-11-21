"""Module for running the training and evaluation experiment.

Writes results.csv to the workspace root (os.getcwd()).
"""
import numpy as np
import pandas as pd
from src.game_env import TicTacToeEnv
from src.q_agent import QAgent
from src.random_opponent import get_random_move
NUM_EPISODES_Q = 10000
DISCOUNT_FACTOR = 0.99
LEARNING_RATE = 0.1
INITIAL_EPSILON = 1.0
EPSILON_DECAY = 0.995
FINAL_EPSILON = 0.05
NUM_EVALUATION_GAMES = 1000
RANDOM_SEED = 42

def run_experiment() -> None:
    """Run Q-learning training and evaluation against random baseline.
    
    1. Seeds numpy with RANDOM_SEED.
    2. Trains Q-agent against random opponent for NUM_EPISODES_Q.
    3. Evaluates Q-agent against random opponent for NUM_EVALUATION_GAMES (win_rate_q, avg_reward_q).
    4. Plays NUM_EVALUATION_GAMES of random-vs-random to get baseline (win_rate_random).
    5. Writes results.csv with metrics: win_rate_q, win_rate_random, avg_reward_q.
    """
    raise NotImplementedError
