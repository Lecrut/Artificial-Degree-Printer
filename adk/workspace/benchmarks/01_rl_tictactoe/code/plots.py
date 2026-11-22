"""Reads experimental results from CSV and generates visualizations of learning curves and win rate comparisons."""
import os
from typing import List
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
FIGURE_DIR: str = 'figures'
RESULTS_FILE: str = 'results.csv'

def generate_plots() -> None:
    """Generate plots from experimental results and save them to disk.

    Reads the ``results.csv`` file (written by :func:`experiment.run_experiment`) 
    which must contain columns: 'method', 'metric', 'value'. The CSV is expected to 
    contain rows for win_rate, draw_rate, loss_rate, mean_reward, and std_dev for 
    each method (e.g., 'q_learning', 'random_baseline').

    Creates two figures:
    1. **Distribution Comparison**: A grouped bar chart comparing the rates of 
       winning, drawing, and losing between the Q-Learning agent and the Baseline.
    2. **Reward Statistics**: A bar chart comparing the mean reward and standard 
       deviation between the methods.

    Saves figures to ``figures/`` directory (creating it if necessary).
    """
    import os
    df = pd.read_csv(RESULTS_FILE)
    os.makedirs(FIGURE_DIR, exist_ok=True)
    fig1, ax1 = plt.subplots(figsize=(8, 5))
    methods = df['method'].unique()
    rate_metric_map = {'win_rate': ('win', 'rate'), 'draw_rate': ('draw', 'rate'), 'loss_rate': ('loss', 'rate')}
    for method in methods:
        subset = df[df['method'] == method]
        y_data = []
        for metric_name in ['win_rate', 'draw_rate', 'loss_rate']:
            val = subset[subset['metric'] == metric_name]['value'].values[0]
            label = rate_metric_map[metric_name][0].title()
            ax1.bar(0, val, width=0.6, color=plt.cm.Set3(val > 0.3)[2], label=label if method == methods[-1] else '', alpha=0.7)
        ax1.axhline(y=1 / 3, color='gray', linestyle='--', alpha=0.5, linewidth=1, label='Theoretical ideal (1/3)')
    ax1.set_xlabel('Game Outcome')
    ax1.set_ylabel('Percentage (%)')
    ax1.set_title('Q-Learning vs Random Baseline: Win/Draw/Loss Rates')
    ax1.legend(title='Method', loc='upper left')
    plt.xticks([0], ['Win / Draw / Loss'])
    fig1.savefig(f'{FIGURE_DIR}/outcome_rates.png', dpi=150, bbox_inches='tight')
    plt.close(fig1)
    fig2, ax2 = plt.subplots(figsize=(8, 6))
    reward_metric_map = {'mean_reward': ('reward', 'mean'), 'std_dev': ('std_dev', 'std')}
    for method in methods:
        subset = df[df['method'] == method]
        y_data = []
        for metric_name in ['mean_reward', 'std_dev']:
            val = subset[subset['metric'] == metric_name]['value'].values[0]
            label = f"{metric_name.replace('_', ' ').title()} : {val:.2f}" if metric_name == 'mean_reward' else f"{metric_name.replace('_', ' ').title()}"
            ax2.bar(0, val, width=0.6, color=plt.cm.Greens(val > 0)[0] if metric_name == 'mean_reward' else '#d4a574', label=label if method == methods[-1] else '', alpha=0.8)
    ax2.set_xlabel('Metric')
    ax2.set_ylabel('Value')
    ax2.set_title('Q-Learning vs Random Baseline: Reward Statistics')
    plt.xticks([0], ['Reward (Mean)', 'Std Dev'])
    fig2.savefig(f'{FIGURE_DIR}/reward_stats.png', dpi=150, bbox_inches='tight')
    plt.close(fig2)

def _plot_distribution_comparison(df: pd.DataFrame) -> None:
    """Visualize win, draw, and loss rates for each method.

    Args:
        df: DataFrame containing aggregated results. Must contain rows for 'win_rate',
        'draw_rate', 'loss_rate' per method.
    """
    import os
    os.makedirs(FIGURE_DIR, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    methods = df['method'].unique()
    rate_metric_map = {'win_rate': ('win', 'rate'), 'draw_rate': ('draw', 'rate'), 'loss_rate': ('loss', 'rate')}
    methods_sorted = sorted(methods)
    x_pos = [0, 1]
    colors_list = []
    labels_list = []
    for method_idx, method in enumerate(methods_sorted):
        subset = df[df['method'] == method]
        ax.bar(x_pos[0], subset.loc[:, 'win_rate'].values[0], width=0.4, color='#377eb8', label=f'{method.title()} Win Rate')
        ax.bar(x_pos[1], subset.loc[:, 'draw_rate'].values[0], width=0.4, color='#a65628', label=f'{method.title()} Draw Rate')
        colors_list.append(['#377eb8', '#a65628'])
        labels_list.append([f'{method.title()}', ''])
    ax.axhline(y=1 / 3, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(['Win', 'Draw'])
    ax.legend(title='Method')
    plt.title('Distribution Comparison: Win/Draw Rates by Method')
    fig.savefig(f'{FIGURE_DIR}/distribution_comparison.png', dpi=150, bbox_inches='tight')
    plt.close(fig)

def _plot_reward_metrics(df: pd.DataFrame) -> None:
    """Visualize Mean Reward and Std Dev for each method.

    Args:
        df: DataFrame containing aggregated results. Must contain rows for 'mean_reward'
        and 'std_dev' per method.
    """
    import os
    os.makedirs(FIGURE_DIR, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 6))
    methods = df['method'].unique()
    methods_sorted = sorted(methods)
    x_pos = [0]
    colors_list = []
    labels_list = []
    for method_idx, method in enumerate(methods_sorted):
        subset = df[df['method'] == method]
        mean_val = subset.loc[:, 'mean_reward'].values[0]
        std_val = subset.loc[:, 'std_dev'].values[0]
        color = plt.cm.Greens(mean_val > 0)[0] if mean_val >= 0 else '#d4a574'
        ax.bar(x_pos, mean_val, yerr=std_val, capsize=5, color=color, label=f'{method.title()}')
        colors_list.append(color)
        labels_list.append(method.title())
    ax.set_xticks(x_pos)
    ax.set_xticklabels(['Mean Reward', 'Std Dev'])
    ax.legend(title='Method')
    plt.title('Reward Statistics: Mean and Standard Deviation by Method')
    fig.savefig(f'{FIGURE_DIR}/reward_metrics.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
