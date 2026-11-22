"""Reads results.csv and generates learning curves and win rate comparison plots into the figures directory."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

FIGURES_DIR: Path = Path('figures')

def plot_results() -> None:
    """Generate convergence curves and comparative win-rate plots from results.csv.

    Reads the file ``results.csv`` from the workspace root. Expects columns 
    ``method``, ``metric``, ``value`` (and optional ``std_dev``, ``n_runs``).

    Produces two figures saved to the ``figures/`` directory:

    1. **win_rate_comparison.png**: Bar chart comparing 'win_rate' metric between 
       the Q-Learning agent and the Random Agent baseline.
    2. **outcome_rates.png**: Grouped bar chart showing win, draw, and loss rates 
       for each method to provide context on the win-rate comparison.

    If ``results.csv`` is missing or lacks required columns, raises an appropriate error.
    """
    # Ensure figures directory exists
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # Read results
    df = pd.read_csv('results.csv')
    
    # Pivot data for easier plotting
    # Index: method, Columns: metric, Values: value
    pivoted_df = df.pivot(index='method', columns='metric', values='value')
    
    methods = pivoted_df.index.tolist()
    
    # --- Plot 1: Win Rate Comparison ---
    if 'win_rate' in pivoted_df.columns:
        win_rates = pivoted_df['win_rate']
        fig, ax = plt.subplots(figsize=(8, 6))
        bars = ax.bar(methods, win_rates.values, color=['skyblue', 'lightcoral'])
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height,
                    f'{height:.3f}',
                    ha='center', va='bottom')
        
        ax.set_title('Win Rate Comparison: Q-Learning vs Random Agent')
        ax.set_ylabel('Win Rate')
        ax.set_xlabel('Method')
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / 'win_rate_comparison.png', dpi=150)
        plt.close(fig)

    # --- Plot 2: Outcome Rates Grouped Bar Chart ---
    fig, ax = plt.subplots(figsize=(8, 6))
    
    n_methods = len(methods)
    # Metrics to plot: win, draw, loss (if present)
    metrics_to_plot = ['win_rate', 'draw_rate', 'loss_rate']
    valid_metrics = [m for m in metrics_to_plot if m in pivoted_df.columns]
    
    if valid_metrics:
        bar_width = 0.25
        indices = range(n_methods)
        
        # Handle case where there might be more methods than standard baseline + agent (e.g. > 2)
        # But usually it's just Q-Learning vs Random.
        
        for i, metric in enumerate(valid_metrics):
            rates = pivoted_df[metric].values
            ax.bar(
                [x + i * bar_width for x in indices],
                rates,
                width=bar_width,
                label=metric.replace('_', ' ').title()
            )
        
        # Set x-ticks to the middle of each group
        ax.set_xticks([x + bar_width for x in indices])
        ax.set_xticklabels(methods)
        ax.set_title('Outcome Rates: Win, Draw, and Loss')
        ax.set_ylabel('Rate')
        ax.set_xlabel('Method')
        ax.legend(title='Metric')
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / 'outcome_rates.png', dpi=150)
        plt.close(fig)