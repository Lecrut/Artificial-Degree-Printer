"""Orchestrates training of the Q-learning agent against a random opponent and evaluates it against the random baseline, saving metrics to results.csv."""
from __future__ import annotations
import os
from typing import List
import numpy as np
import pandas as pd
from agents.q_agent import QLearningAgent
from agents.random_agent import RandomAgent
from environment.tictactoe_env import TicTacToeEnv
N_EPISODES: int = 50000
N_EVALUATION_GAMES: int = 2000
LEARNING_RATE: float = 0.1
DISCOUNT_FACTOR: float = 0.95
EXPLORATION_EPSILON_TRAINING: float = 0.1
EXPLORATION_EPSILON_INFERENCE: float = 0.0
SEED: int = 42
RESULTS_FILENAME: str = 'results.csv'

def _play_game(env: TicTacToeEnv, agent_x: QLearningAgent | RandomAgent, agent_o: QLearningAgent | RandomAgent, epsilon: float) -> int:
    """
    Simulate a single game of Tic-Tac-Toe between two agents.

    The environment starts with Player X moving first. The function tracks the
    outcome from the perspective of the agent playing as Player X (`agent_x`).

    Args:
        env: A reset TicTacToeEnv instance ready for a new game.
        agent_x: The agent controlling Player X (+1).
        agent_o: The agent controlling Player O (-1).
        epsilon: Exploration rate used by `agent_x` if it is a QLearningAgent.
                 Ignored if `agent_x` is a RandomAgent.

    Returns:
        An integer result code from the perspective of Player X (`agent_x`):
        1 if Player X wins,
        0 if the game ends in a draw,
        -1 if Player O wins.
    """
    raise NotImplementedError

def _compute_metrics(results: List[int]) -> tuple[float, float, float]:
    """
    Calculate win, draw, and loss rates from a list of game results.

    Args:
        results: A list of integers (1 for win, 0 for draw, -1 for loss)
                 from the perspective of the primary agent.

    Returns:
        A tuple (win_rate, draw_rate, loss_rate), where each rate is a float in [0, 1].
        The sum of the three rates will be approximately 1.0.
    """
    raise NotImplementedError

def run_study() -> None:
    """
    Execute the full training and evaluation pipeline for the Q-Learning agent.

    This function:
    1. Initializes the TicTacToe environment, the Q-learning agent, and the Random baseline agent.
    2. Trains the Q-agent against a random opponent for `N_EPISODES` episodes.
       It tracks the training reward to monitor convergence.
    3. Evaluates the trained Q-agent against the Random Agent in `N_EVALUATION_GAMES` games,
       averaging results over both playing positions (X and O).
    4. Evaluates the Random Agent against itself in `N_EVALUATION_GAMES` games to establish a baseline.
    5. Aggregates the results into a pandas DataFrame with columns `method`, `metric`, `value`,
       and saves it to `results.csv` in the current working directory.

    Metrics saved:
        - Method 'q_learning':
            - win_rate: Win rate against Random Agent (averaged over X and O positions).
            - draw_rate: Draw rate against Random Agent.
            - loss_rate: Loss rate against Random Agent.
        - Method 'random_agent':
            - win_rate: Win rate against another Random Agent.
            - draw_rate: Draw rate against another Random Agent.
            - loss_rate: Loss rate against another Random Agent.
    """
    raise NotImplementedError
