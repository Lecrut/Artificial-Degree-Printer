from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from typing import List

def generate_plots(output_dir: str='.') -> List[str]:
    """
    Generate comparison charts from metric results.
    Reads results.csv (columns: method, metric, value) from the output directory.
    Plots mean F1 vs Mean AUC for Multi-Channel Bio-Signals and Detection Delay per method.
    Saves figures to output_dir/figures/.
    """
    import os
    Path.mkdir(Path(output_dir), exist_ok=True)
    results_path = Path(output_dir) / 'results.csv'
    if not results_path.exists():
        raise FileNotFoundError(f'Results file {results_path} not found. Run experiment first.')
    df = pd.read_csv(results_path)
    if df.empty:
        return []
    groupby_col = 'method' if 'method' in df.columns else None
    if not groupby_col:
        raise ValueError(f"Missing required columns: expected 'method', 'metric', 'value'. Found: {df.columns.tolist()}")
    figures = []
    plt.figure(figsize=(8, 6))
    if 'mean_f1_score' not in df.columns:
        raise ValueError(f"Missing required columns: expected 'mean_f1_score', found: {df.columns.tolist()}")
    f1_means = df.groupby(groupby_col)['mean_f1_score'].mean().sort_values(ascending=True)
    methods = f1_means.index
    values = f1_means.values
    bars = plt.bar(methods, values, color='#2ca02c')
    plt.xlabel('Method')
    plt.ylabel('Mean F1 Score')
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2.0, height, f'{height:.4f}', ha='center', va='bottom')
    plt.title('Comparison of Mean F1 Scores')
    plt.xticks(rotation=45)
    plt.tight_layout()
    figures_dir = Path(output_dir) / 'figures'
    figures_dir.mkdir(exist_ok=True)
    fig_path = figures_dir / 'mean_f1_comparison.png'
    plt.savefig(fig_path)
    plt.close()
    figures.append(str(fig_path))
    return figures
