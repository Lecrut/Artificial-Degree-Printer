"""Plotting functions for experiment results."""
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os

def plot_results() -> None:
    """Reads results.csv and saves figures to figures/ directory."""
    import matplotlib.pyplot as plt
    os.makedirs('figures', exist_ok=True)
    df = pd.read_csv('results.csv')
    if df.empty:
        return
    methods = df['method'].unique()
    metrics_to_plot = ['path_cost', 'expanded_nodes']
    for method in methods:
        fig, ax = plt.subplots()
        subset = df[df['method'] == method]
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        for _, row in subset.iterrows():
            metric_name = row['metric']
            ax.plot(row['value'], label=metric_name.replace('_', ' '))
        ax.legend(title='Metric')
        ax.set_title(f'Results: {method}')
        ax.grid(True)
        plt.tight_layout()
        fig.savefig(f'figures/{method}_results.png', dpi=300, bbox_inches='tight')
        plt.close()
