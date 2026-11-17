"""Utilities to visualize experiment results.

This module processes CSV logs from the Q-Learning Tic-Tac-Toe experiment,
generating convergence and win-rate figures.
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
pd.set_option('display.max_columns', None)
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['axes.linewidth'] = 1.2
plt.rcParams['grid.alpha'] = 0.3

def generate_plots(output_dir: str) -> list[str]:
    """Generate convergence and win-rate plots from CSV logs.

    Reads the results CSV file containing method, metric, value rows,
generates a convergence plot for win rate over time, and a win-rate comparison
if multiple methods are present. Saves figures to `output_dir/figures`.
Returns a list of figure file paths.

Args:
    output_dir (str): Directory where figures will be saved.

Returns:
    list[str]: List of paths to generated figure files.
"""
    import seaborn as sns
    fig_dir = Path(output_dir) / 'figures'
    fig_dir.mkdir(parents=True, exist_ok=True)
    results_path = Path(output_dir) / 'results.csv'
    if not results_path.exists():
        raise FileNotFoundError(f'Results file not found at {results_path}')
    df = pd.read_csv(results_path)
    figures_generated = []
    if 'method' in df.columns and 'value' in df.columns:
        time_col = None
        numeric_cols = [c for c in df.columns if df[c].apply(lambda x: isinstance(x, (int, float)) and (not pd.isna(x))).any()]
        if 'step' in numeric_cols:
            time_col = 'step'
        if time_col:
            aggregated_df = df.groupby('method', group_keys=False).apply(lambda g: g.sort_values(time_col)['value']).reset_index()
            plt.figure()
            sns.lineplot(data=aggregated_df, x=time_col, y='value')
            ax = plt.gca()
            ax.set_title('Win Rate Convergence over Steps')
            ax.set_xlabel('Steps')
            ax.set_ylabel('Win Rate')
            fig_name = f'convergence.png'
            os.makedirs(fig_dir, exist_ok=True)
            plt.savefig(f'{fig_dir}/{fig_name}')
            plt.close()
            figures_generated.append(f'figures/{fig_name}')
        else:
            aggregated_df = df.groupby('method', group_keys=False)['value'].mean().reset_index()
            sns.barplot(data=aggregated_df, x='method', y='value')
            ax = plt.gca()
            ax.set_title('Mean Win Rate by Method')
            ax.set_xlabel('Method')
            ax.set_ylabel('Win Rate')
            fig_name = f'win_rate_comparison.png'
            os.makedirs(fig_dir, exist_ok=True)
            plt.savefig(f'{fig_dir}/{fig_name}')
            plt.close()
            figures_generated.append(f'figures/{fig_name}')
    return figures_generated
