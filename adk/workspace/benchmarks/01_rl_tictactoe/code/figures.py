"""Reads train_log.csv and results.csv to generate learning curves and win-rate comparison charts."""
import os
from constants import TRAIN_LOG_CSV_PATH, RESULTS_CSV_PATH, FIGURES_DIR

def generate_figures() -> None:
    """Reads training logs and experiment results to generate and save figures.

    Creates the figures directory if it does not exist, plots the average reward
    over episodes from train_log.csv and win/draw/loss rates from results.csv,
    then saves them to FIGURES_DIR.
    """
    import pandas as pd
    import matplotlib.pyplot as plt
    import numpy as np
    from pathlib import Path
    figures_path = Path(FIGURES_DIR)
    figures_path.mkdir(parents=True, exist_ok=True)
    log_df = pd.read_csv(TRAIN_LOG_CSV_PATH)
    if 'episode' not in log_df.columns or 'reward' not in log_df.columns:
        raise ValueError("train_log.csv must have 'episode' and 'reward' columns")
    avg_reward = log_df.groupby('episode')['reward'].mean()
    episodes = avg_reward.index
    rewards = avg_reward.values
    plt.figure(figsize=(8, 5))
    plt.plot(episodes, rewards, marker='o', linestyle='-', linewidth=1.5, markersize=2)
    plt.title('Average Reward per Episode')
    plt.xlabel('Episode')
    plt.ylabel('Reward')
    plt.grid(True, linestyle='--', alpha=0.5)
    reward_fig_path = figures_path / 'reward_curve.png'
    plt.savefig(reward_fig_path, bbox_inches='tight')
    plt.close()
    results_df = pd.read_csv(RESULTS_CSV_PATH)
    if 'method' not in results_df.columns or 'value' not in results_df.columns:
        raise ValueError("results.csv must have 'method' and 'value' columns")
    if 'metric' not in results_df.columns:
        raise ValueError("results.csv must have a 'metric' column")
    target_metrics = ['win_rate_vs_random', 'draw_rate_vs_random', 'loss_rate_vs_random']
    filtered_results = results_df[results_df['metric'].isin(target_metrics)]
    if filtered_results.empty:
        raise ValueError('results.csv does not contain the required metrics')
    agents = sorted(filtered_results['method'].unique())
    n_agents = len(agents)
    n_metrics = len(target_metrics)
    plt.figure(figsize=(10, 6))
    bar_width = 0.2
    index = np.arange(n_agents)
    for i, metric in enumerate(target_metrics):
        metric_data = filtered_results[filtered_results['metric'] == metric]
        values = []
        for agent in agents:
            row_match = metric_data[metric_data['method'] == agent]
            val = row_match['value'].iloc[0] if len(row_match) > 0 else 0.0
            values.append(val)
        offset = i * bar_width
        plt.bar(index + offset, values, width=bar_width, label=metric)
    plt.title('Win/Draw/Loss Rates vs Random Baseline')
    plt.xlabel('Method')
    plt.ylabel('Rate (%)')
    plt.xticks(index + bar_width * (n_metrics - 1) / 2, agents)
    plt.legend(title='Metric')
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    rates_fig_path = figures_path / 'win_loss_rates_comparison.png'
    plt.savefig(rates_fig_path, bbox_inches='tight')
    plt.close()
