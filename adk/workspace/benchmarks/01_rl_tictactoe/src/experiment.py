"""Main experiment runner and entry point."""
import random
from typing import Any, List, Dict
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from src.config import get_default_config
from src.game_environment import GameEnvironment, RandomOpponentAgent
from src.q_learner import Q_Learning_Agent
from src.plot_results import plot_comparison_results

def run_experiment() -> None:
    """Entry point: runs the full experiment with configurable parameters from config.py.
    Writes results to a CSV and generates a comparison chart."""
    config = get_default_config()
    rng = np.random.default_rng(seed=config.seed)
    results_data: list[dict[str, Any]] = []
    episodes_per_run = config.episodes_per_train
    for run_id in range(1, config.num_runs + 1):
        env = GameEnvironment()
        random_opponent = RandomOpponentAgent(board=env.reset().board)
        q_agent = Q_Learning_Agent(state_encoder=env.get_state_hash, discount_factor=config.gamma, learning_rate=config.learning_rate, epsilon_start=config.epsilon_start, epsilon_end=config.epsilon_end, epsilon_decay=config.epsilon_decay)
        for _ in range(episodes_per_run):
            state = env.reset()
            q_agent.train_episode(random_opponent.get_move)
        num_eval_episodes = config.num_evaluation_episodes
        wins_qlearner = 0
        draws_qlearner = 0
        for _ in range(num_eval_episodes):
            state = env.reset()
            winner: int | None = None
            draw_flag = False
            turn = 1
            max_turns = config.max_turns
            while not draw_flag and turn <= max_turns:
                if turn % 2 == 1:
                    action = q_agent.select_action(env.get_state_hash(state))
                    next_state = env.apply_action(1, action)
                else:
                    available_moves = env.get_available_moves(state.board)
                    if len(available_moves) == 0:
                        draw_flag = True
                        break
                    move_idx = rng.integers(0, len(available_moves))
                    action = list(available_moves)[move_idx]
                    next_state = env.apply_action(2, action)
                    winner = env.check_winner(next_state)[0]
                    if winner == 1:
                        pass
                    elif winner == 2:
                        pass
                    draw_flag = env.check_winner(next_state)[1] == 'draw'
                turn += 1
            if winner is None and (not draw_flag):
                final_winner, final_reason = env.check_winner(state.board)
                if final_winner != 0:
                    winner = final_winner
                else:
                    draw_flag = True
            is_win_q = winner == 1
            is_draw_q = draw_flag
            wins_qlearner += int(is_win_q)
            draws_qlearner += int(is_draw_q)
        win_rate_q = wins_qlearner / num_eval_episodes
        draw_rate_q = draws_qlearner / num_eval_episodes
        loss_rate_q = 1 - win_rate_q - draw_rate_q
        metrics_run = {'run_id': run_id, 'method_qlearner_win_rate': win_rate_q, 'method_qlearner_draw_rate': draw_rate_q, 'baseline_win_rate_vs_q': 0.5, 'convergence_step': None}
        results_data.append(metrics_run)
    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / 'results.csv'
    df = pd.DataFrame(results_data)
    df.to_csv(csv_path, index=False)
    plot_comparison_results(results_data, csv_path, figure_name='TicTacToe_QLearning_vs_Random')
