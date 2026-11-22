"""Generuje wykresy z wyników eksperymentu (porównanie metod, rozkład błędów) i zapisuje je w figures/."""
import os
from typing import List

def plot_figures() -> None:
    """Generuje i zapisuje wykresy porównujące metody detekcji anomalii."""
    import os
    import pandas as pd
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    os.makedirs('figures', exist_ok=True)
    df = pd.read_csv('results.csv')
    methods = df['method'].unique().tolist()
    metrics_list = ['auc_roc', 'f1_score']
    if any((m not in df.columns for m in metrics_list)):
        raise ValueError(f"Missing expected metric columns. Found: {[c for c in df.columns if c != 'method']}, Expected: {metrics_list}")
    avg_data = {}
    std_data = {}
    metric_order = ['auc_roc', 'f1_score']
    for method in methods:
        method_df = df[df['method'] == method]
        values = {}
        stds = {}
        for m in metric_order:
            col_name = f'{m}_value'
            if 'std_dev' in df.columns:
                col_std = f'{m}_std_dev'
            else:
                col_std = None
            val = method_df[col_name].iloc[0]
            std_val = method_df[col_std].iloc[0] if col_std is not None else np.nan
            values[m] = val
            stds[m] = std_val
        avg_data[method] = {m: values[m] for m in metric_order}
        std_data[method] = {m: stds[m] for m in metric_order}
    fig, ax1 = plt.subplots(figsize=(8, 6))
    colors = {'auc_roc': '#1f77b4', 'f1_score': '#ff7f0e'}
    methods_list = list(avg_data.keys())
    bars = []
    ax1.bar(methods_list, [avg_data[m][m] for m in metric_order for m in methods_list], color=[colors[m] for m in metric_order], tick_label=methods_list)
    ax1.set_ylabel('Mean Value', fontweight='bold')
    plt.setp(ax1.get_yticklabels(), fontsize=10, rotation=90)
    ax1.tick_params(axis='x', labelsize=10)
    ax1.tick_params(axis='y', labelsize=10)
    plt.close(fig)
    fig2, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={'height': 4})
    bars_x = methods_list
    bar_height = 0.6
    colors = ['#1f77b4', '#ff7f0e']
    ax1.barh(methods_list, [avg_data[m]['auc_roc'] for m in methods_list], color=colors[0])
    ax1.bar(methods_list[::-1], [avg_data[m]['f1_score'] for m in methods_list], color=colors[1], alpha=0.6)
    ax1.set_xlabel('Methods')
    ax1.set_ylabel('Performance Metric Values')
    ax1.invert_xaxis()
    fig3, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(14, 6))
    indices = range(len(methods_list))
    x_vals = indices + 0.5
    for i, method in enumerate(methods_list):
        ax_left.bar(x_vals[i], [avg_data[method]['auc_roc']], color='#1f77b4', label=method if i == 0 else None, yerr=[std_data[method]['auc_roc'], std_data[method]['auc_roc']])
        ax_left.bar(x_vals[i] + 0.5, [avg_data[method]['f1_score']], color='#ff7f0e', label=method, yerr=[std_data[method]['f1_score'], std_data[method]['f1_score']])
    ax_left.set_xlabel('Method')
    ax_left.set_ylabel('Mean Score (AUC/F1)')
    ax_left.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
    plt.tight_layout()
    fig3.savefig('figures/comparison_bar.png', dpi=300, bbox_inches='tight')
    plt.close(fig3)
    fig4 = plt.figure(figsize=(8, 6))
    ax_error = fig4.add_subplot(111)
    colors2 = ['#e7b800', '#8dd3c7']
    for i, method in enumerate(methods_list):
        ax_error.bar(x_vals[i], [avg_data[method]['auc_roc']], color=colors2[0], yerr=[std_data[method]['auc_roc'], std_data[method]['auc_roc']])
        ax_error.bar(x_vals[i] + 1.2, [avg_data[method]['f1_score']], color=colors2[1], yerr=[std_data[method]['f1_score'], std_data[method]['f1_score']])
    ax_error.set_xlabel('Method')
    ax_error.set_ylabel('Performance Score with Standard Deviation')
    ax_error.grid(axis='y', linestyle='--', alpha=0.7)
    fig4.savefig('figures/error_bars.png', dpi=300, bbox_inches='tight')
    plt.close(fig4)
