"""Generates publication-quality figures for the thesis based on experiment results."""
import seaborn as sns
from matplotlib.patches import Rectangle
import os
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def generate_figures() -> None:
    """Generate and save figures based on `results.csv`."""
    import os
    import sys
    import pandas as pd
    import figures
    results_path = 'results.csv'
    if not os.path.exists(results_path):
        print(f"Warning: '{results_path}' not found. Skipping figure generation.", file=sys.stderr)
        return
    df = pd.read_csv(results_path)
    os.makedirs('figures', exist_ok=True)
    f1_path = 'figures/f1_distribution.png'
    _plot_metric_distribution(df, 'f1_score', f1_path)
    auc_path = 'figures/auc_distribution.png'
    _plot_metric_distribution(df, 'auc_score', auc_path)
    signal_path = 'figures/signal_example.png'
    _plot_signal_example(signal_path)

def _plot_metric_distribution(df: pd.DataFrame, metric_name: str, save_path: str) -> None:
    """Draw a box plot for a specific metric across methods.

    Filters `df` to rows where `metric` equals `metric_name`. Expects a `value`
    column and a `method` column. If no data is available for the metric, prints
    a warning and returns without saving.

    Args:
        df: The full results DataFrame.
        metric_name: The literal key in `df['metric']` to filter by (e.g., 'f1_score').
        save_path: File path where the PNG will be saved.
    """
    filtered_df = df[df['metric'] == metric_name][['method', 'value']].copy()
    if len(filtered_df) == 0:
        import sys
        print(f"Warning: No data found for metric '{metric_name}'.", file=sys.stderr)
        return
    methods = filtered_df['method'].unique().tolist()
    plot_data = [filtered_df.loc[filtered_df['method'] == m, 'value'].values for m in methods]
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    sns.set_theme(context='paper')
    fig, ax = plt.subplots(figsize=(8, 6))
    boxplot = ax.boxplot(plot_data, labels=methods, patch_artist=True, showfliers=False)
    ax.set_title(f'Distribution of {metric_name} across Methods')
    ax.set_ylabel(metric_name)
    fig.tight_layout()
    plt.savefig(save_path, bbox_inches='tight')
    plt.close()

def _plot_signal_example(save_path: str) -> None:
    """Plot a synthetic signal with injected anomalies for thesis context.

    Generates a static example (same seed every run) of multi-channel physiological 
    data to illustrate what the detector sees. Saves as PNG.

    Args:
        save_path: File path where the PNG will be saved.
    """
    np.random.seed(42)
    T = 1000
    n_channels = 4
    channels = {}
    anomaly_idx = [350, 720]
    for i in range(n_channels):
        if i == 0:
            t = np.arange(T)
            data = np.sin(2 * np.pi * 1.0 / T * t) + 0.5 * np.random.randn(len(t))
            channels[i] = data
        else:
            channels[i] = np.random.randn(T)
    anomaly_mask = np.zeros((n_channels, T), dtype=bool)
    for idx in anomaly_idx:
        for ch in range(n_channels):
            anomaly_mask[ch, idx] = True
            anomaly_mask[ch, idx + 10] = True
    fig, ax = plt.subplots(figsize=(12, 6))
    for i in range(n_channels):
        y = channels[i]
        ax.plot(range(T), y[:250], color='black', linewidth=0.8)
        if hasattr(y, '__iter__') and len(y) > 1:
            ax.plot(range(len(y)), y, color='blue', marker='v', markersize=10, label=f'Ch{i}')
    for idx in anomaly_idx:
        if i == 0:
            ax.fill(xmin=idx, xmax=idx + 50, ymin=-2.5, ymax=0, alpha=0.7, color='red', label=f'Anomaly at {idx}')
            break
        else:
            ax.axvline(x=idx, ymin=1, ymax=-1, color='blue', linewidth=2)
    ax.set_title("Synthetic Physiological Signal with Injected Anomalies\n(Demonstrating the detector's input view)")
    ax.set_xlabel('Time Step')
    ax.set_ylabel('Value')
    ax.legend()
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, bbox_inches='tight')
    plt.close()
