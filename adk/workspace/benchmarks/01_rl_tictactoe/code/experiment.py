"""Executes the training and evaluation loops for Q-Learning on Tic-Tac-Toe.

This module orchestrates the interaction between `TicTacToeEnv`, `QLearningAgent`,
and `RandomBaselineAgent` to generate metrics required by the thesis.
"""
import numpy as np
import pandas as pd
from environment import TicTacToeEnv, RandomAgent
from agent import QLearningAgent
from config import N_EPISODES, N_TEST_GAMES, N_RUNS, SEED_BASE

def _play_single_game(env: TicTacToeEnv, agents: tuple) -> dict:
    """Execute one game between two agents and return its result metrics.

    Plays a single full episode of Tic-Tac-Toe. The environment is reset at the start.
    Agents take turns choosing actions until termination (win/loss/draw).
    Crucially, it ensures that only valid moves (into empty cells) are executed to
    prevent infinite loops caused by invalid state updates.

    Args:
        env: A fresh or reset Gymnasium-compatible TicTacToeEnv instance.
        agents: A tuple of two objects implementing `select_action(state) -> int`.
                The first agent plays as 'X' (state 1), the second as 'O' (state 2).

    Returns:
        metrics: A dictionary containing results for the first agent (agent1):
            - 'reward' (float): Terminal reward received by agent1 (+1.0 win, 0.0 draw, -1.0 loss).
            - 'done' (bool): Always True at return.
    """
    obs, _ = env.reset()
    player = 1
    done = False
    while not done:
        current_agent_idx = 0 if player == 1 else 1
        agent = agents[current_agent_idx]
        empty_cells = np.where(obs == 0)[0]
        if len(empty_cells) == 0:
            break
        raw_action = int(agent.select_action(obs))
        if raw_action not in empty_cells:
            action = int(np.random.choice(empty_cells))
        else:
            action = raw_action
        obs, reward, terminated, truncated, _ = env.step(action)
        done = terminated or truncated
        player = 2 if player == 1 else 1
    return {'reward': reward, 'done': True}

def _evaluate_agent(q_agent: QLearningAgent, env_template: TicTacToeEnv) -> dict:
    """Evaluate the trained Q-Agent against the Random Baseline for N_TEST_GAMES.

    Sets the Q-Agent's epsilon to 0 (greedy policy) before evaluation.
    Aggregates win, loss, and draw rates for the Q-Agent.

    Args:
        q_agent: The trained QLearningAgent instance. Its epsilon is temporarily set to 0.
        env_template: A TicTacToeEnv instance used to create new copies via `type(env)()` 
                      or simply reset if stateless enough (assuming fresh env per game for independence).

    Returns:
        metrics: A dictionary containing evaluation statistics for the Q-Agent:
            - 'avg_reward' (float): Mean terminal reward for Q-Agent.
            - 'win_rate' (float): Fraction of test games won by Q-Agent.
            - 'loss_rate' (float): Fraction of test games lost by Q-Agent.
            - 'draw_rate' (float): Fraction of test games drawn.
    """
    win_count = 0
    loss_count = 0
    draw_count = 0
    total_reward_sum = 0.0
    q_agent.epsilon = 0.0
    for _ in range(N_TEST_GAMES):
        env = TicTacToeEnv()
        agents = (q_agent, RandomAgent())
        result = _play_single_game(env, agents)
        if result['reward'] > 0:
            win_count += 1
        elif result['reward'] < 0:
            loss_count += 1
        else:
            draw_count += 1
        total_reward_sum += result['reward']
    return {'avg_reward': total_reward_sum / N_TEST_GAMES, 'win_rate': win_count / N_TEST_GAMES, 'loss_rate': loss_count / N_TEST_GAMES, 'draw_rate': draw_count / N_TEST_GAMES}

def _train_one_run(run_seed: int) -> tuple:
    """Run one repetition of training and evaluation.

    1. Set global seed for reproducibility within this run.
    2. Initialize Agent and Environment.
    3. Train for N_EPISODES episodes against RandomAgent.
    4. Evaluate trained agent against RandomAgent.

    Args:
        run_seed: The random seed for this specific repetition.

    Returns:
        metrics: A dictionary containing training and evaluation statistics:
            - 'avg_reward' (float): Mean terminal reward during the last 10% of training episodes.
            - 'win_rate' (float): Win rate in evaluation phase.
            - 'loss_rate' (float): Loss rate in evaluation phase.
            - 'draw_rate' (float): Draw rate in evaluation phase.
        history: A list of dicts with keys 'episode', 'reward' for training history.
    """
    from agent import TOTAL_CELLS
    np.random.seed(run_seed)
    agent = QLearningAgent(state_size=TOTAL_CELLS, alpha=0.1, gamma=0.9, epsilon=0.2)
    env = TicTacToeEnv()
    recent_rewards = []
    history = []
    for episode_idx in range(N_EPISODES):
        obs, _ = env.reset()
        player = 1
        done = False
        total_reward = 0.0
        prev_obs = obs
        while not done:
            current_agent_idx = 0 if player == 1 else 1
            agent_obj = agent if current_agent_idx == 0 else RandomAgent()
            empty_cells = np.where(obs == 0)[0]
            if len(empty_cells) == 0:
                break
            raw_action = int(agent_obj.select_action(obs))
            if raw_action not in empty_cells:
                action = int(np.random.choice(empty_cells))
            else:
                action = raw_action
            obs, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            total_reward += reward
            if current_agent_idx == 0:
                agent.update(prev_obs, action, reward, obs, done)
            prev_obs = obs
            player = 2 if player == 1 else 1
        history.append({'episode': episode_idx, 'reward': total_reward})
        if episode_idx >= int(N_EPISODES * 0.9):
            recent_rewards.append(total_reward)
    avg_reward = sum(recent_rewards) / len(recent_rewards) if recent_rewards else 0.0
    eval_metrics = _evaluate_agent(agent, env)
    return ({'avg_reward': avg_reward, **eval_metrics}, history)

def run_experiment() -> pd.DataFrame:
    """Run the full training and evaluation experiment and return aggregated results.

    This function acts as the entrypoint for the experiment. It performs ``N_RUNS``
    independent repetitions to account for stochasticity. In each repetition:
    1. Initializes `TicTacToeEnv`, `QLearningAgent` (with epsilon-greedy), and uses `RandomAgent` as opponent.
    2. Trains the Q-Learning agent for ``N_EPISODES`` episodes against the random baseline.
    3. Evaluates the trained `QLearningAgent` against `RandomBaselineAgent` for ``N_TEST_GAMES``
       games using a greedy policy (epsilon=0).

    Aggregates metrics across all runs into a tidy DataFrame with columns:
    'method', 'metric', 'value', 'std_dev', 'n_runs'.

    Metrics included:
        - 'avg_reward' (training): Mean episode return during the last 10% of training.
        - 'win_rate' (eval): Win rate of Q-Learning vs Random in test games.
        - 'loss_rate' (eval): Loss rate of Q-Learning vs Random in test games.
        - 'draw_rate' (eval): Draw rate of Q-Learning vs Random in test games

    Writes the aggregated results to 'results.csv' in the workspace root.

    Returns:
        results_df: A pandas DataFrame with shape ``(num_metrics, 5)`` 
                    containing the aggregated mean and std_dev over ``N_RUNS`` repetitions for each metric.
                    The 'method' column will be 'Q-Learning'.
    """
    all_histories = []
    results_rows = []
    for run_idx in range(N_RUNS):
        run_seed = SEED_BASE + run_idx
        metrics_run, history = _train_one_run(run_seed)
        all_histories.extend(history)
        results_rows.append({'method': 'Q-Learning', 'metric': 'avg_reward', 'value': metrics_run['avg_reward']})
        results_rows.append({'method': 'Q-Learning', 'metric': 'win_rate', 'value': metrics_run['win_rate']})
        results_rows.append({'method': 'Q-Learning', 'metric': 'loss_rate', 'value': metrics_run['loss_rate']})
        results_rows.append({'method': 'Q-Learning', 'metric': 'draw_rate', 'value': metrics_run['draw_rate']})
    df = pd.DataFrame(results_rows)
    aggregated = []
    for metric_name in df['metric'].unique():
        values = df[df['metric'] == metric_name]['value']
        sd_val = values.std(ddof=1) if len(values) > 1 else 0.0
        aggregated.append({'method': 'Q-Learning', 'metric': metric_name, 'value': values.mean(), 'std_dev': sd_val, 'n_runs': len(values)})
    results_df = pd.DataFrame(aggregated)
    import os
    results_path = os.path.join(os.getcwd(), 'results.csv')
    results_df.to_csv(results_path, index=False)
    history_df = pd.DataFrame(all_histories)
    history_path = os.path.join(os.getcwd(), 'training_history.csv')
    history_df.to_csv(history_path, index=False)
    return results_df
