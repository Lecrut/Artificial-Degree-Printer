"""
Evaluation module to compute metrics against the random baseline.
Reads configuration from config.py.
"""
import numpy as np
from typing import List, Tuple
import tictactoe_env
import q_learning_agent
import random_agent
import config

def run_evaluation_episode(q_learner: q_learning_agent.QLearner, env: tictactoe_env.TicTacToeEnv) -> Tuple[float, float]:
    """
    Run a single evaluation episode and return (win_rate_vs_random, draw_rate_vs_random).
    Since we compare against the SAME game (AI vs Random), we compute win rates relative to random play.
    Actually, the metric is: 'how well does it learn' -> Win Rate vs Random Baseline performance?
    The prompt asks: 'h
    """
    total_reward = 0.0
    runs = max(config.NUM_EVALUATION_RUNS, 1) * 5
    wins = 0
    draws = 0
    losses = 0
    total_rewards = []
    for _ in range(runs):
        state = env.reset()
        done = False
        current_reward = 0.0
        step_count = 0
        while not done:
            env.get_current_player()
            available_moves = [i for i in range(9) if env.is_valid_move(i)]
            if not available_moves:
                break
            action = None
            if step_count % 2 == 0:
                state_key = env.get_state_key(state)
                action = q_learner.choose_action(state_key)
                if not env.is_valid_move(action):
                    action = random.choice(available_moves)
            else:
                random_agent_obj = random_agent.RandomAgent()
                action = random_agent_obj.choose_action(available_moves)
            new_state, reward, done = env.step(action)
            state = new_state
            current_reward += reward
            step_count += 1
        total_rewards.append(current_reward)
        winner = env.get_winner()
        if winner == 1:
            wins += 1
        elif winner == 2:
            losses += 1
        else:
            draws += 1
            total_reward += current_reward
    win_rate = wins / runs
    draw_rate = draws / runs
    return (win_rate, draw_rate)
