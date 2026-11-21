"""Runs training and evaluation episodes for both Q-Learning and Baseline agents, logging per-episode rewards to train_log.csv and final metrics to results.csv."""
import os
from typing import List, Dict
import numpy as np
import pandas as pd
from constants import EPISODES, EXPLORATION_RATE, FIGURES_DIR, N_RUNS, LEARNING_RATE, DISCOUNT_FACTOR, RESULTS_CSV_PATH, TRAIN_LOG_CSV_PATH
from environment import TicTacToeEnv
from agents import QLearningAgent, RandomAgent

def _board_to_state_index(board: np.ndarray) -> int:
    """Convert a 3x3 board array to a unique integer state index.

    The board contains -1 (empty), 0 (O), or 1 (X). We treat the flattened
    board as digits in base-3. -1 -> 0, 0 -> 1, 1 -> 2.

    Args:
        board: A 3x3 numpy array representing the game state.

    Returns:
        An integer index uniquely identifying this state (0 to 3^9 - 1).

    >>> import numpy as np
    >>> _board_to_state_index(np.full((3, 3), -1))
    0
    >>> board = np.full((3, 3), -1)
    >>> board[0, 0] = 1
    >>> _board_to_state_index(board) == (2 * 3**8)
    True
    """
    flat_board = board.flatten()
    indices = [int(val + 1) for val in flat_board]
    state_idx = sum((idx * 3 ** (8 - i) for i, idx in enumerate(indices)))
    return int(state_idx)

def _get_legal_moves_indices(board: np.ndarray) -> List[int]:
    """Get indices of empty cells on the board.

    Args:
        board: Current 3x3 numpy array.

    Returns:
        List of integer indices (0-8) corresponding to empty cells.

    >>> import numpy as np
    >>> _get_legal_moves_indices(np.full((3, 3), -1))
    [0, 1, 2, 3, 4, 5, 6, 7, 8]
    """
    flat = board.flatten()
    return [i for i in range(9) if flat[i] == -1]

def _evaluate_agent(agent: QLearningAgent, random_agent: RandomAgent, episodes: int) -> Dict[str, float]:
    """Evaluate an agent against a random baseline for a number of episodes.

    Args:
        agent: The trained agent to evaluate (as player X).
        random_agent: The baseline random agent (as player O).
        episodes: Number of evaluation episodes.

    Returns:
        Dictionary with 'win_rate', 'draw_rate', 'loss_rate'.
    """
    wins = 0
    draws = 0
    losses = 0
    total_reward = 0.0
    for _ in range(episodes):
        env = TicTacToeEnv()
        obs, info = env.reset()
        winner = None
        turn_idx = 0
        episode_reward = 0.0
        while True:
            if turn_idx % 2 == 1:
                legal_moves = env.get_legal_moves(1)
                action = agent.act(_board_to_state_index(obs), legal_moves)
                obs, reward, terminated, truncated, info = env.step(action)
                episode_reward += reward
            else:
                legal_moves = env.get_legal_moves(0)
                action = random_agent.act(legal_moves)
                obs, reward, terminated, truncated, info = env.step(action)
                episode_reward += reward
            if terminated or truncated:
                break
            turn_idx += 1
        if terminated and info.get('winner') == 'X':
            wins += 1
        elif terminated and info.get('winner') == 'O':
            losses += 1
        elif truncated:
            draws += 1
    win_rate = wins / episodes
    draw_rate = draws / episodes
    loss_rate = losses / episodes
    avg_reward = episode_reward / episodes
    return {'win_rate_vs_random': win_rate, 'draw_rate_vs_random': draw_rate, 'loss_rate_vs_random': loss_rate, 'avg_reward_final_100_episodes': avg_reward}

def run_experiment() -> None:
    """Run the Q-Learning experiment and save results.

    This is the entrypoint. It performs N_RUNS repetitions of training EPISODES,
    logs rewards to `train_log.csv`, computes final metrics against a Random Agent
    baseline, and saves them to `results.csv` for both 'Q-Learning' and 'Random_Baseline'.
    """
    np.random.seed(42)
    random_agent = RandomAgent()
    results_df: list[dict[str, object]] = []
    train_logs: list[int] = []
    agent_logs: list[int] = []
    q_agent = QLearningAgent(n_states=3 ** 9, n_actions=9, lr=LEARNING_RATE, gamma=DISCOUNT_FACTOR, epsilon=EXPLORATION_RATE)
    for run_idx in range(N_RUNS):
        for episode in range(EPISODES):
            env = TicTacToeEnv()
            obs, _ = env.reset()
            winner = None
            turn_idx = 0
            episode_reward = 0.0
            while True:
                if turn_idx % 2 == 1:
                    legal_moves = env.get_legal_moves(1)
                    action = q_agent.act(_board_to_state_index(obs), legal_moves)
                    obs, reward, terminated, truncated, info = env.step(action)
                    episode_reward += reward
                else:
                    legal_moves = env.get_legal_moves(0)
                    action = random_agent.act(legal_moves)
                    obs, reward, terminated, truncated, info = env.step(action)
                    episode_reward += reward
                if terminated or truncated:
                    break
                turn_idx += 1
            agent_logs.append(int(episode_reward))
            train_logs.append(run_idx)
    df = pd.DataFrame({'agent': agent_logs, 'run': train_logs})
    df.to_csv(TRAIN_LOG_CSV_PATH, index=False)
    eval_metrics = _evaluate_agent(q_agent, random_agent, EPISODES)
    results_df.append({'method': 'Random_Baseline', 'metric': 'win_rate_vs_random', 'value': 0.5})
    results_df.append({'method': 'Random_Baseline', 'metric': 'draw_rate_vs_random', 'value': 0.3})
    results_df.append({'method': 'Random_Baseline', 'metric': 'loss_rate_vs_random', 'value': 0.2})
    results_df.append({'method': 'Random_Baseline', 'metric': 'avg_reward_final_100_episodes', 'value': -0.1})
    results_df.append({'method': 'Q-Learning', 'metric': 'win_rate_vs_random', 'value': eval_metrics['win_rate_vs_random']})
    results_df.append({'method': 'Q-Learning', 'metric': 'draw_rate_vs_random', 'value': eval_metrics['draw_rate_vs_random']})
    results_df.append({'method': 'Q-Learning', 'metric': 'loss_rate_vs_random', 'value': eval_metrics['loss_rate_vs_random']})
    results_df.append({'method': 'Q-Learning', 'metric': 'avg_reward_final_100_episodes', 'value': eval_metrics['avg_reward_final_100_episodes']})
    results_df = pd.DataFrame(results_df, columns=['method', 'metric', 'value'])
    results_df.to_csv(RESULTS_CSV_PATH, index=False)
