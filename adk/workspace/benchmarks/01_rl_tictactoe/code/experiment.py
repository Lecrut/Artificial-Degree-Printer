"""Orchestrates the training of the Q-Learning agent and its evaluation against both itself (during play) and the random baseline, aggregating results into a CSV file."""
from __future__ import annotations
import csv
import os
from pathlib import Path
from typing import List, Tuple, Dict
import numpy as np
from environment import TicTacToeEnv
from agent import QLearningAgent
from baseline_agent import RandomAgent
N_EPISODES: int = 1000
RANDOM_BASLINE_GAMES: int = 1000
SEED: int = 42
EpsilonDecayRate: float = 0.995
MinEpsilon: float = 0.01
OUTPUT_CSV: str = 'results.csv'
WORKSPACE_ROOT: Path = Path('.')

def run_experiment() -> None:
    """Run the full reinforcement learning experiment and save results to CSV.

    This function performs three main phases:
    1. Training: The Q-Learning agent plays against a random opponent for 
       ``N_EPISODES`` episodes, updating its Q-table after each move.
    2. Baseline Evaluation: A game played between two RandomAgents is simulated 
       for ``RANDOM_BASLINE_GAMES`` games to establish a win/draw/loss distribution 
       for purely random play.
    3. Final Evaluation: The trained Q-Learning agent plays against the same 
       RandomAgent for ``RANDOM_BASLINE_GAMES`` games to measure its performance.

    Results are aggregated into rows with columns: 
    ``method, metric, value, std_dev, n_runs``.
    Methods are "Q-Learning_vs_Random" and "Random_vs_Random". Metrics are 
    "win_rate", "draw_rate", "loss_rate" (relative to the agent named first). 

    The output CSV is written to the workspace root at ``results.csv``.
    """
    raise NotImplementedError

def _evaluate_agent(env: TicTacToeEnv, p1_agent, p2_agent, n_games: int, rng: np.random.Generator) -> Dict[str, float]:
    """Evaluate an agent playing as player 1 against another agent (player 2).

    Args:
        env: The TicTacToe environment instance.
        p1_agent: The agent playing as Player X (moves first). Must have ``act(state)``.
        p2_agent: The agent playing as Player O. Must have ``act(state)``.
        n_games: Number of games to simulate.
        rng: Random number generator for reproducibility.

    Returns:
        A dictionary with keys 'p1_wins', 'p2_wins', 'draws', each mapping to the 
        count of such outcomes observed during the evaluation.
    """
    raise NotImplementedError
