"""Generates visualizations of learning curves and performance metrics comparing Q-Learning agent against a random baseline for the thesis."""

def plot_results() -> None:
    """Reads 'results.csv' and generates visualizations for the thesis."""
    import pandas as pd
    import matplotlib.pyplot as plt
    import numpy as np
    import os
    from matplotlib.font_manager import FontProperties
    df = pd.read_csv('results.csv')
    fig_dir = 'figures/'
    os.makedirs(fig_dir, exist_ok=True)
    FontProperties(family='sans-serif', size=12).set_property('fontfamily', 'monospace')
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.size'] = 10
    lc_df = df[df['metric'] == 'mean_reward_per_episode'].sort_values('episode_index')
    q_learning_lc = lc_df[lc_df['method'] == 'q_learning']
    random_agent_lc = lc_df[lc_df['method'] == 'random_agent']
    fig, ax = plt.subplots(figsize=(10, 6))
    if len(q_learning_lc) > 0 and len(random_agent_lc) > 0:
        ax.plot(q_learning_lc['episode_index'], q_learning_lc['value'], marker='o', label='Q-Learning', linewidth=2)
        ax.plot(random_agent_lc['episode_index'], random_agent_lc['value'], marker='s', label='Random Agent', linestyle='--', alpha=0.7)
        ax.set_xlabel('Episode Index')
        ax.set_ylabel('Mean Reward per Episode')
        ax.set_title('Learning Curves: Q-Learning vs Random Agent')
        ax.legend()
        ax.grid(True, alpha=0.3)
    else:
        ax.text(0.5, 0.5, 'No data available for learning curves.', transform=ax.transData, fontsize=12, ha='center', va='center')
    plt.savefig(f'{fig_dir}learning_curves.png', bbox_inches='tight', dpi=300)
    plt.close()
    metrics_df = df[df['metric'].isin(['win_rate', 'draw_rate', 'loss_rate'])]
    methods = ['q_learning', 'random_agent']
    metric_names = [m for m in ['win_rate', 'draw_rate', 'loss_rate'] if m in metrics_df['metric'].values]
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = []
    bar_positions = np.arange(len(methods))
    width = 0.35
    colors = ['#2E86AB', '#A4373A']
    for i, metric_name in enumerate(metric_names):
        q_data = metrics_df[metrics_df['method'] == 'q_learning' & metrics_df['metric'] == metric_name]['value']
        r_data = metrics_df[metrics_df['method'] == 'random_agent' & metrics_df['metric'] == metric_name]['value']
        if len(q_data) > 0 and len(r_data) > 0:
            bp = ax.bar(bar_positions[i], q_data.values, width, label=f'{metric_name} (Q-Learning)', color=colors[0])
            bars.append(bp)
            ax.bar(bar_positions[i] + width / 2, r_data.values, width, label=f'{metric_name} (Random Agent)', color=colors[1], alpha=0.7)
    ax.set_xlabel('Method')
    ax.set_ylabel('Rate (%)')
    ax.set_title('Final Performance Metrics Comparison')
    ax.set_xticks(bar_positions)
    ax.set_xticklabels(methods)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    plt.savefig(f'{fig_dir}final_metrics_comparison.png', bbox_inches='tight', dpi=300)
    plt.close()
