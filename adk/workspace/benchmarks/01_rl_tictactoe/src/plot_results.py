"""Script to load experiment results and generate comparison plots."""
import numpy as np
from collections import Counter
from typing import List, Tuple
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from config import OUTPUT_CSV, METRICS_TO_REPORT
import os
import pandas as pd
FIGURE_PATHS: List[str] = ['figures/comparison_chart.pdf', 'figures/comparison_chart.png']

def generate_plots(output_dir: str='.') -> List[str]:
    """Read CSV results, compute aggregates, and save plot figures to output_dir.
    Returns the paths of saved figure files."""
    import os
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    try:
        df = pd.read_csv(OUTPUT_CSV)
    except FileNotFoundError:
        raise ValueError(f"Results file '{OUTPUT_CSV}' not found.")
    if df.empty:
        raise ValueError('Results dataframe is empty.')
    required_cols = ['method', 'value', 'std_dev']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f'Missing required columns: {missing_cols}')
    method_data = df['method'].tolist()
    metric_values = df['value'].tolist()
    std_devs = df['std_dev'].tolist()
    q_values: List[float] = []
    std_list_q: List[float] = []
    r_values: List[float] = []
    for idx, method in enumerate(method_data):
        if method == 'Q-Learning':
            q_values.append(float(metric_values[idx]))
            std_list_q.append(float(std_devs[idx]))
        elif method == 'Random':
            r_values.append(float(metric_values[idx]))
    win_rate_agent: float = 0.0
    win_rate_base: float = 0.0
    if q_values:
        win_rate_agent = np.mean(q_values)
    if r_values:
        win_rate_base = np.mean(r_values)
    std_error_agent: float = 0.0
    if len(q_values) > 1:
        std_error_agent = np.std(q_values, ddof=1)
    else:
        std_error_agent = abs(float(std_list_q[0])) if std_list_q else 0.0
    full_output_path = os.path.join(output_dir, 'figures')
    fig_paths: List[str] = []
    if not os.path.exists(full_output_path):
        os.makedirs(full_output_path)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle('Tic-Tac-Toe Q-Learning Experiment Results', fontsize=16)
    bar_x = ['Q-Learning (Agent)', 'Random Opponent']
    bar_y = [win_rate_agent, win_rate_base]
    axes[0].bar(bar_x, bar_y, color=['skyblue', 'lightgray'], edgecolor='black')
    axes[0].set_ylabel('Win Rate (%)')
    axes[0].set_title('Win Rate Comparison')
    axes[0].legend(['Q-Learning', 'Random'])
    reward_values = q_values if len(q_values) > 1 else [win_rate_agent]
    std_rew_stddev = std_list_q if len(std_list_q) > 1 else [std_error_agent]
    axes[1].plot(range(len(reward_values)), reward_values, linestyle='-', marker='o', color='green')
    if len(std_rew_stddev) > 0 and std_rew_stddev[0] is not None:
        error_y_low = np.array([reward_val - std for reward_val, std in zip(reward_values, std_rew_stddev)])
        error_y_high = np.array([reward_val + std for reward_val, std in zip(reward_values, std_rew_stddev)])
        axes[1].fill_between(range(len(reward_values)), error_y_low, error_y_high, alpha=0.3, color='green')
    axes[1].set_ylabel('Reward')
    axes[1].set_title('Average Reward Per Episode (Q-Learning)')
    axes[1].tick_params(labelrotation=-45)
    plt.tight_layout()
    pdf_path = os.path.join(full_output_path, 'comparison_chart.pdf')
    fig_paths.append(pdf_path)
    plt.savefig(pdf_path, bbox_inches='tight', dpi=150)
    plt.close()
    png_path = os.path.join(full_output_path, 'comparison_chart.png')
    fig_paths.append(png_path)
    plt.savefig(png_path, bbox_inches='tight', dpi=150)
    return fig_paths
