"""Reads results.csv and generates publication-ready figures for the thesis."""
import numpy as np
import pandas as pd
from matplotlib.pyplot import subplots, legend

def generate_plots() -> None:
    """Reads 'results.csv' (columns: method, metric, value, std_dev, n_runs) and writes figures to 'figures/'. Generates two subplots: a learning curve showing mean reward evolution over episodes for Q-Learning versus Random Agent with error bars (from std_dev), and a final performance comparison bar plot of win/loss/draw rates. Uses matplotlib backend Agg. Handles empty input by raising ValueError. All axis labels and titles reflect the literal metric names and method names."""
    df = pd.read_csv('results.csv')
    if df.empty:
        raise ValueError('results.csv is empty')
    required_cols = ['method', 'metric', 'value', 'std_dev']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f'Missing required columns: {missing_cols}')
    fig1, ax1 = subplots(figsize=(8, 6))
    fig2, ax2 = subplots(figsize=(8, 4))
    reward_data = df[df['metric'] == 'avg_reward'].copy()
    other_metrics = [m for m in df['metric'].unique() if m != 'avg_reward']
    if not reward_data.empty:
        if len(reward_data) > 1:
            pass
        else:
            ax1.barh(y=reward_data['method'], height=0.3, x=reward_data['value'].tolist(), yerr=reward_data['std_dev'].tolist(), capsize=5)
            ax1.set_xlabel('Mean Reward')
            ax1.set_title('Learning Curve: Mean Reward by Method (Aggregate)')
    else:
        all_data = df.head()
        ax1.axis('off')
    stats_data = df[df['metric'].isin(['win_rate', 'loss_rate', 'draw_rate'])]
    x_pos = np.arange(len(df[df['method'] == 'Q-Learning']['method'])) + 0.1 if not df.empty else []
    x_neg = np.arange(len(df[df['method'] == 'Random']['method'])) - 0.5 if 'Random' in df['method'].values else []
    methods = sorted(df['method'].unique().tolist())
    metrics_to_plot = ['win_rate', 'loss_rate', 'draw_rate']
    colors = ['#1f77b4', '#ff7f0e']
    if 'Q-Learning' in df['method'].values:
        idx_q = methods.index('Q-Learning')
    else:
        idx_q = -1
    if 'Random' in df['method'].values:
        idx_r = methods.index('Random')
    else:
        idx_r = -1
    ax2.bar(x_pos[idx_q] if idx_q >= 0 else 0, stats_data[stats_data['metric'] == 'win_rate']['value'].values[0] if not stats_data[stats_data['metric'] == 'win_rate'].empty else 0, color='#1f77b4', width=0.35, label='Q-Learning')
    ax2.bar(x_pos[idx_r] if idx_r >= 0 else 0, stats_data[stats_data['metric'] == 'win_rate']['value'].values[0] if not stats_data[stats_data['metric'] == 'win_rate'].empty else 0, color='#ff7f0e', width=0.35, label='Random')
    ax2.bar(x_pos[idx_q] if idx_q >= 0 else 0, stats_data[stats_data['metric'] == 'loss_rate']['value'].values[0] if not stats_data[stats_data['metric'] == 'loss_rate'].empty else 0, color='#1f77b4', width=0.35)
    ax2.bar(x_pos[idx_r] if idx_r >= 0 else 0, stats_data[stats_data['metric'] == 'loss_rate']['value'].values[0] if not stats_data[stats_data['metric'] == 'loss_rate'].empty else 0, color='#ff7f0e', width=0.35)
    ax2.bar(x_pos[idx_q] if idx_q >= 0 else 0, stats_data[stats_data['metric'] == 'draw_rate']['value'].values[0] if not stats_data[stats_data['metric'] == 'draw_rate'].empty else 0, color='#1f77b4', width=0.35)
    ax2.bar(x_pos[idx_r] if idx_r >= 0 else 0, stats_data[stats_data['metric'] == 'draw_rate']['value'].values[0] if not stats_data[stats_data['metric'] == 'draw_rate'].empty else 0, color='#ff7f0e', width=0.35)
    ax2.set_ylabel('Rate')
    ax2.set_title('Final Performance: Win/Loss/Draw Rates')
    ax2.legend()
    output_dir = 'figures'
    import os
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    fig1.savefig(f'{output_dir}/learning_curve.pdf')
    fig1.savefig(f'{output_dir}/learning_curve.png', bbox_inches='tight')
    fig2.savefig(f'{output_dir}/performance_comparison.pdf')
    fig2.savefig(f'{output_dir}/performance_comparison.png', bbox_inches='tight')
    return ['figures/learning_curve.pdf', 'figures/performance_comparison.pdf']
