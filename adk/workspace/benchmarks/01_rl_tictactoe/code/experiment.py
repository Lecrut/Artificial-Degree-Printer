"""Executes the Q-Learning training and evaluation pipeline for Tic-Tac-Toe against a random opponent, computing metrics including average episode reward and writing results to CSV."""
from config import TOTAL_EPISODES, TEST_EPISODES, LEARNING_RATE, DISCOUNT_FACTOR, INITIAL_EPSILON, FINAL_EPSILON, EPSILON_DECAY, SEED
from tictactoe_env import TicTacToeEnv
from q_learning_agent import QLearningAgent
from random_agent import RandomAgent
from game_loop import play_game
import numpy as np
import pandas as pd

def run_experiment() -> None:
    """Runs the complete training and evaluation experiment. It initializes a QLearningAgent with hyperparameters from config and a RandomAgent for the opponent. It runs TOTAL_EPISODES episodes of play_game against the random opponent to train the agent's Q-table, then resets epsilon and evaluates the trained policy in TEST_EPISODES episodes against the same random opponent. It aggregates metrics into results.csv with columns method, metric, value. For 'q_learning' method: win_rate (fraction of games won by Q-agent), draw_rate (fraction of draws), loss_rate (fraction of games lost by Q-agent), and avg_reward_per_episode (mean cumulative undiscounted reward for Q-agent over the episode). For 'random_baseline' method: it computes the same set of metrics against itself to establish a performance baseline. Uses numpy.random.default_rng(SEED) for all random number generation to ensure reproducibility. The function returns no value."""
    raise NotImplementedError
