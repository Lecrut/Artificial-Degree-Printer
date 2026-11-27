"""Entrypoint module that orchestrates the full training and evaluation experiment pipeline for a Q-Learning agent playing Tic-Tac-Toe."""
import csv
import math
import os
from typing import Any, Dict, List, Tuple
from trainer import train_policy
from evaluator import evaluate_match, compute_metrics, compute_baseline_stats
from q_agent import QAgent
from baseline_agent import RandomAgent
RESULTS_FILENAME: str = 'results.csv'
FIGURES_DIRNAME: str = 'figures'
N_EPISODES: int = 5000
REPETITIONS: int = 5
INITIAL_EPSILON: float = 1.0
FINAL_EPSILON: float = 0.05
LEARNING_RATE: float = 0.1
GAMMA: float = 0.95
N_MATCHES_PER_EVAL: int = 200
BASELINE_N_MATCHES: int = 1000
SEED_OFFSET: int = 42

def _epsilon_decay_fn(episode: int) -> float:
    """Linearly decays epsilon from INITIAL_EPSILON to FINAL_EPSILON over N_EPISODES. Returns the current epsilon value for the given episode index (0-indexed). If episode >= N_EPISODES, returns FINAL_EPSILON."""
    if episode >= N_EPISODES:
        return FINAL_EPSILON
    progress: float = episode / (N_EPISODES - 1)
    return INITIAL_EPSILON + progress * (FINAL_EPSILON - INITIAL_EPSILON)

def run_experiment() -> None:
    """Runs the complete experiment: training, evaluation, and saving results to CSV.

    Executes `train_policy` for `REPETITIONS` times with different seeds to generate trained agents and training stats. For each repetition:
    1. Trains a QAgent using `trainer.train_policy` against a Random Baseline.
    2. Evaluates the trained agent against a `RandomAgent` using `evaluator.evaluate_match`.
    3. Computes metrics using `evaluator.compute_metrics`.

    Aggregates the resulting metrics (agent_win_rate, agent_draw_rate, agent_loss_rate, avg_episode_reward) across repetitions. Computes mean and standard deviation where applicable.

    Writes these rows to `results.csv` in the current working directory with headers: method, metric, value, std_dev, n_runs. The 'method' column distinguishes between 'q_agent' (trained agent) and 'baseline' (random self-play). Creates the `figures/` directory if it does not exist."""
    from evaluator import compute_baseline_stats
    metric_values: Dict[str, List[float]] = {'avg_episode_reward': [], 'agent_win_rate': [], 'agent_draw_rate': [], 'agent_loss_rate': []}
    for i in range(REPETITIONS):
        rep_seed: int = SEED_OFFSET + i
        training_stats: Dict[str, Any] = train_policy(n_episodes=N_EPISODES, env_seed=rep_seed)
        final_avg_reward: float = training_stats.get('avg_reward_window', 0.0)
        trained_agent: QAgent = training_stats['trained_agent']
        eval_counts: Dict[str, int] = evaluate_match(agent_a=trained_agent, agent_b_class=RandomAgent, n_matches=N_MATCHES_PER_EVAL, seed=rep_seed)
        metrics: Dict[str, float] = compute_metrics(wins=eval_counts['wins_agent_a'], losses=eval_counts['losses_agent_a'], draws=eval_counts['draws'], n_matches=N_MATCHES_PER_EVAL)
        metric_values['avg_episode_reward'].append(final_avg_reward)
        metric_values['agent_win_rate'].append(metrics['win_rate'])
        metric_values['agent_draw_rate'].append(metrics['draw_rate'])
        metric_values['agent_loss_rate'].append(metrics['loss_rate'])
    baseline_metrics: Dict[str, float] = compute_baseline_stats(n_matches=BASELINE_N_MATCHES, seed=SEED_OFFSET + REPETITIONS)
    baseline_win_rate: float = baseline_metrics.get('win_rate', 0.0)
    metric_values['baseline_win_rate'] = [baseline_win_rate]

    def calc_stats(values: List[float]) -> Tuple[float, float, int]:
        n: int = len(values)
        if n == 0:
            return (0.0, 0.0, 0)
        mean_val: float = sum(values) / n
        if n < 2:
            std_val: float = 0.0
        else:
            variance: float = sum(((x - mean_val) ** 2 for x in values)) / (n - 1)
            std_val: float = math.sqrt(variance)
        return (mean_val, std_val, n)
    rows: List[List[Any]] = []
    for metric_name, values in metric_values.items():
        mean_val, std_val, n_runs = calc_stats(values)
        method_type: str = 'q_agent' if metric_name != 'baseline_win_rate' else 'baseline'
        rows.append([method_type, metric_name, mean_val, std_val, n_runs])
    with open(RESULTS_FILENAME, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['method', 'metric', 'value', 'std_dev', 'n_runs'])
        for row in rows:
            writer.writerow(row)
    os.makedirs(FIGURES_DIRNAME, exist_ok=True)
