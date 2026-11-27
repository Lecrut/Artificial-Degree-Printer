"""Provides evaluation utilities for Tic-Tac-Toe agents, including match simulation and metric computation."""
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from environment import TicTacToeEnv, WIN_REWARD, LOSS_REWARD, DRAW_REWARD
from q_agent import QAgent
from baseline_agent import RandomAgent

def evaluate_match(agent_a: Any, agent_b: Any, env_template: TicTacToeEnv, n_matches: int, epsilon: float) -> Dict[str, int]:
    """Simulates a series of matches between two agents and returns the result counts.

    Agents alternate roles: for matches where index i is even, agent_a plays X (first mover);
    where i is odd, agent_a plays O. This balances first-move advantage.
    For QAgent instances, epsilon is passed to choose_action; for RandomAgent, it is ignored.

    Returns:
        dict: A dictionary with keys 'wins_agent_a' (int), 'wins_agent_b' (int), and 'draws' (int).
              The sum equals n_matches. If an agent raises an exception, the match is skipped.
    """
    if n_matches == 0:
        return {'wins_agent_a': 0, 'wins_agent_b': 0, 'draws': 0}
    wins_a = 0
    wins_b = 0
    draws = 0
    for match_idx in range(n_matches):
        env = type(env_template)()
        obs, _ = env.reset(seed=None)
        done = False
        truncated = False
        if match_idx % 2 == 0:
            player_x_agent = agent_a
            player_o_agent = agent_b
        else:
            player_x_agent = agent_b
            player_o_agent = agent_a
        turn_is_x = True
        while not (done or truncated):
            possible_moves = env._get_available_moves()
            if not possible_moves:
                break
            if turn_is_x:
                active_agent = player_x_agent
            else:
                active_agent = player_o_agent
            try:
                if isinstance(active_agent, QAgent):
                    action = active_agent.choose_action(obs, possible_moves, epsilon)
                else:
                    action = active_agent.choose_action(obs, possible_moves)
            except Exception:
                break
            obs, reward, done, truncated, info = env.step(action)
            turn_is_x = not turn_is_x
        if done:
            winner = info.get('winner', 0)
            if match_idx % 2 == 0:
                if winner == 1:
                    wins_a += 1
                elif winner == -1:
                    wins_b += 1
                else:
                    draws += 1
            elif winner == -1:
                wins_a += 1
            elif winner == 1:
                wins_b += 1
            else:
                draws += 1
        else:
            draws += 1
    return {'wins_agent_a': wins_a, 'wins_agent_b': wins_b, 'draws': draws}

def compute_metrics(win_rate: float, win_count: int, draw_count: int, loss_count: int, n_matches: int, baseline_win_rate: float=0.0, baseline_draw_rate: float=0.0) -> Dict[str, float]:
    """Computes performance metrics from raw match counts and rates."""
    if n_matches == 0:
        return {'agent_win_rate': 0.0, 'agent_draw_rate': 0.0, 'agent_loss_rate': 0.0, 'vs_baseline_advantage': -baseline_win_rate, 'vs_baseline_draw_advantage': -baseline_draw_rate}
    loss_rate = loss_count / n_matches
    return {'agent_win_rate': win_rate, 'agent_draw_rate': draw_count / n_matches, 'agent_loss_rate': loss_rate, 'vs_baseline_advantage': win_rate - baseline_win_rate, 'vs_baseline_draw_advantage': draw_count / n_matches - baseline_draw_rate}
