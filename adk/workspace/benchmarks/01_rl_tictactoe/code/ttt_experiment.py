"""Experiment entrypoint to train Q-Learning agent against a random opponent."""
import os
import pandas as pd
from ttt_config import MAX_EPISODES, TEST_EPISODES, LEARNING_RATE, DISCOUNT_FACTOR, EPSILON_START, EPSILON_END, EPSILON_DECAY, SEED, OUTPUT_DIR
from ttt_env import Board, get_random_move
from ttt_agent import Agent

def run_experiment() -> None:
    """Runs the training loop and evaluation against a random player.

    Trains an agent for MAX_EPISODES against a uniform random opponent,
    then evaluates it over TEST_EPISODES. Saves win/loss/draw rates to CSV in OUTPUT_DIR.
    
    Metrics computed:
        - win_rate: Proportion of games won by the agent (playing as X).
        - draw_rate: Proportion of draws.
        - loss_rate: Proportion of games lost.
    """
    raise NotImplementedError
