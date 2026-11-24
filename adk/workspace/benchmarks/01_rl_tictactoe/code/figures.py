"""Reads results.csv and generates the required visualizations for the thesis."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def plot_results() -> None:
    """Reads `results.csv` and writes figures into `figures/`."""
    os.makedirs('figures', exist_ok=True)
    try:
        results_df = pd.read_csv('results.csv')
    except FileNotFoundError:
        raise RuntimeError("Results file 'results.csv' not found.")
    if results_df.empty or 'method' not in results_df.columns:
        print('No valid data found in results.csv.')
        return
    pivot_df = results_df.pivot_table(index='method', columns='metric', values='value', aggfunc='mean')
    rate_cols = ['win_rate', 'draw_rate', 'loss_rate']
    baseline_cols = ['baseline_win_rate', 'baseline_draw_rate', 'baseline_loss_rate']
    metric_labels = {'win_rate': 'Win Rate', 'draw_rate': 'Draw Rate', 'loss_rate': 'Loss Rate', 'avg_reward': 'Avg Reward', 'baseline_win_rate': 'Baseline Win', 'baseline_draw_rate': 'Baseline Draw', 'baseline_loss_rate': 'Baseline Loss'}
    active_rate_cols = [c for c in rate_cols if c in pivot_df.columns]
    active_baseline_cols = [c for c in baseline_cols if c in pivot_df.columns]
    if not active_rate_cols:
        print('No rate metrics found in results.csv to plot.')
        return
    grouped_means = pivot_df[active_rate_cols]
    grouped_baselines = pivot_df[active_baseline_cols] if active_baseline_cols else pd.DataFrame()
    methods = list(grouped_means.index)
    num_methods = len(methods)
    if num_methods == 0:
        print('No methods found in results.csv to plot.')
        return
    plt.figure(figsize=(10, 6))
    colors = ['#2ecc71', '#f1c40f', '#e74c3c']
    bottom = np.zeros(num_methods)
    for i, metric in enumerate(active_rate_cols):
        if metric not in grouped_means.columns:
            continue
        data = grouped_means[metric].values
        label = metric_labels.get(metric, metric)
        plt.bar(methods, data, bottom=bottom, label=label, color=colors[min(i, len(colors) - 1)])
        bottom += data
    plt.ylabel('Rate')
    plt.title('Final Win/Draw/Loss Rates Comparison by Method')
    plt.legend(title='Outcome')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('figures/final_rates_comparison.png', bbox_inches='tight')
    plt.close()
    plt.figure(figsize=(10, 6))
    if 'win_rate' in grouped_means.columns and (not grouped_baselines.empty) and ('baseline_win_rate' in grouped_baselines.columns):
        ql_win_rates = grouped_means['win_rate'].values
        baseline_win_rates = grouped_baselines['baseline_win_rate'].values
        x_pos = np.arange(num_methods)
        width = 0.35
        plt.bar(x_pos - width / 2, ql_win_rates, width, label='Q-Learning')
        plt.bar(x_pos + width / 2, baseline_win_rates, width, label='Baseline (Random)')
        plt.xticks(x_pos, methods)
        plt.title('Win Rate: Q-Learning vs Baseline')
        plt.legend()
    elif 'win_rate' in grouped_means.columns:
        plt.bar(methods, grouped_means['win_rate'].values)
        plt.ylabel('Win Rate')
        plt.title('Q-Learning Win Rate by Method')
        plt.xticks(rotation=45)
    else:
        plt.text(0.5, 0.5, 'No Win Rate Data', ha='center', va='center')
        plt.title('Win Rate Plot (Missing Data)')
    plt.ylim(0, 1.05)
    plt.tight_layout()
    plt.savefig('figures/win_rate_vs_baseline.png', bbox_inches='tight')
    plt.close()
    if 'avg_reward' in grouped_means.columns and (not grouped_baselines.empty):
        plt.figure(figsize=(10, 6))
        ql_rewards = grouped_means['avg_reward'].values
        plt.bar(methods, ql_rewards)
        plt.ylabel('Average Reward')
        plt.title('Average Reward per Game by Method')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('figures/avg_reward_comparison.png', bbox_inches='tight')
        plt.close()
    print('Figures saved to figures/ directory.')
