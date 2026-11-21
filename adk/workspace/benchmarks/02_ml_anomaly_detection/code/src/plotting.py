"""Visualization module for experimental results."""
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

def plots() -> None:
    """Read results.csv and generate figures in figures/ directory.

    Generates plots of F1 distribution across seeds and average confusion matrices.
    Reads from 'results.csv' (columns: method, metric, value, std_dev, n_runs).
    Saves figures to 'figures/' directory.
    """
    import os
    import numpy as np
    os.makedirs('figures', exist_ok=True)
    try:
        df = pd.read_csv('results.csv')
    except FileNotFoundError:
        raise RuntimeError("Experiment not run yet. Run 'src/experiment.py:run_experiment'.")
    if 'F1' in df['metric'].values:
        f1_data = df[df['metric'] == 'F1'][['method', 'value', 'std_dev']].copy()
        f1_data.columns = ['Method', 'Mean_F1', 'Std_F1']
        fig, ax = plt.subplots(figsize=(8, 6))
        colors = {'Robust_Ensemble': '#2E86AB', 'Baseline_Z': '#D95F02'}
        methods = f1_data['Method'].unique()
        bars = []
        for method in methods:
            mask = f1_data['Method'] == method
            bar_width = 0.35
            x = np.arange(len(methods))
            ax.bar(x, f1_data.loc[mask, 'Mean_F1'], yerr=f1_data.loc[mask, 'Std_F1'], width=bar_width, label=method, color=colors.get(method, '#C73E1D'), edgecolor='black')
            bars.append((x, method, f1_data.loc[mask, 'Mean_F1']))
        ax.set_xlabel('Detection Method', fontsize=12)
        ax.set_ylabel('F1 Score', fontsize=12)
        ax.set_title('F1 Score Performance Across Methods (With Standard Deviation)', fontsize=14)
        ax.legend()
        ax.grid(axis='y', alpha=0.7)
        plt.tight_layout()
        fig.savefig('figures/F1_comparison.png', dpi=300, bbox_inches='tight')
    metric_plots = {'Macro-Precision': ['Precision', 'F1'], 'Accuracy': ['Precision', 'Recall']}
    fig, ax = plt.subplots(figsize=(8, 6))
    methods_sorted = sorted(methods)
    x = np.arange(len(methods_sorted))
    for metric_name in ['Precision', 'Recall']:
        if metric_name in df['metric'].values:
            data = df[df['metric'] == metric_name][['method', 'value', 'std_dev']].copy()
            data.columns = ['Method', 'Mean_' + metric_name, 'Std_' + metric_name]
            bars = []
            for method in methods_sorted:
                mask = data['Method'] == method
                val = data.loc[mask, 'Mean_' + metric_name].values[0]
                err = data.loc[mask, 'Std_' + metric_name].values[0]
                color = '#F38181' if method == 'Robust_Ensemble' else '#6B9080'
                bar = ax.bar(method, val, yerr=err, capsize=5, color=color, edgecolor='black')
                bars.append((method, val))
            if metric_name in ['Precision', 'Recall']:
                ax.set_ylabel(f'Average {metric_name.capitalize()}', fontsize=12)
            ax.set_title(f'{metric_name} Across Methods (With Standard Deviation)', fontsize=14)
    ax.axhline(y=0.5, color='red', linestyle='--', alpha=0.7, label='Random/Threshold 0.5')
    ax.legend()
    ax.grid(axis='y', alpha=0.7)
    plt.tight_layout()
    fig.savefig('figures/Metrics_comparison.png', dpi=300, bbox_inches='tight')
