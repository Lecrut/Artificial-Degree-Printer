"""Reads results.csv and generates visualizations for the thesis."""
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from typing import Optional

def create_figures() -> None:
    """Reads the aggregated results from the default `results.csv` location and writes publication-quality figures into the default `figures/` directory."""
    import os
    cwd: str = os.getcwd()
    results_path: str = os.path.join(cwd, 'results.csv')
    figures_dir: str = os.path.join(cwd, 'figures')
    os.makedirs(figures_dir, exist_ok=True)
    try:
        df: pd.DataFrame = pd.read_csv(results_path)
    except FileNotFoundError:
        import logging
        logging.warning('results.csv not found. Skipping plot generation.')
        return
    except Exception as e:
        import logging
        logging.warning(f'Error reading results.csv: {e}')
        return
    if df.empty:
        import logging
        logging.warning('results.csv is empty. No figures to generate.')
        return
    if 'metric' not in df.columns or 'value' not in df.columns:
        import logging
        logging.warning("results.csv missing required 'metric' or 'value' columns.")
        return
    if 'std_dev' in df.columns and 'n_runs' in df.columns:
        pivot_df: pd.DataFrame = df.pivot(index='method', columns='metric', values='value')
    else:
        pivot_df = df.pivot(index='method', columns='metric', values='value')
    methods: list[str] = sorted(df['method'].unique())
    metrics: list[str] = sorted(df['metric'].unique())
    if not methods or not metrics:
        return
    ax1: plt.Axes
    fig1, ax1 = plt.subplots(figsize=(8, 6))
    x_pos: list[float] = [i for i in range(len(methods))]
    width: float = 0.35
    palette: list[str] = sns.color_palette('husl', len(metrics))
    all_std_devs: dict[str, dict[str, Optional[float]]] = {}
    for _, row in df.iterrows():
        m: str = row['method']
        met: str = row['metric']
        if 'std_dev' in df.columns:
            std_val: float = float(row['std_dev'])
        else:
            std_val = 0.0
        all_std_devs[m, met] = std_val if not pd.isna(std_val) else 0.0
    for i, metric in enumerate(metrics):
        values: list[float] = [pivot_df.loc[m, metric] for m in methods if metric in pivot_df.columns]
        std_vals: list[float] = [all_std_devs.get((m, metric), 0.0) for m in methods]
        ax1.bar([p + i * width for p in x_pos], values, width=width, label=metric.upper(), color=palette[i], yerr=[max(v, 0.0) for v in std_vals], capsize=4, edgecolor='black')
    ax1.set_xticks([p + width / 2 for p in x_pos])
    ax1.set_xticklabels(methods)
    ax1.set_ylabel('Score')
    ax1.set_title('Performance Metrics Comparison (Mean ± Std Dev)')
    ax1.legend()
    fig1.tight_layout()
    fig1.savefig(os.path.join(figures_dir, 'performance_comparison.png'), dpi=300)
    plt.close(fig1)
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    heatmap_data: pd.DataFrame = pivot_df.loc[methods, metrics] if all((m in pivot_df.columns for m in metrics)) else None
    if heatmap_data is not None and (not heatmap_data.empty):
        sns.heatmap(heatmap_data, annot=True, fmt='.4f', cmap='viridis', ax=ax2, xticklabels=metrics, yticklabels=methods)
        ax2.set_title('Metric Values Heatmap')
        fig2.tight_layout()
        fig2.savefig(os.path.join(figures_dir, 'performance_heatmap.png'), dpi=300)
        plt.close(fig2)
