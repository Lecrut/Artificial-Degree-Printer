"""Reads results.csv and score exports to generate comparison plots into figures/."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import seaborn as sns
from pathlib import Path


def plot_results() -> None:
    """Generate visualization plots from experiment results and exported scores.

    Reads `results.csv` (with columns `method`, `metric`, `value`) from the workspace root
    to create a grouped bar chart comparing key metrics (AUC_ROC, F1_SCORE) between
    baseline and subspace methods. It also reads the exported score data from 
    `figures/scores_for_plots.csv` (via `score_exporter.py`) to plot the distribution
    of anomaly scores overlaid with ground truth labels.

    The function ensures the output directory exists and saves:
    1. `figures/metrics_comparison.png`: Grouped bar chart of mean metric values.
    2. `figures/score_distribution.png`: Histogram/Density plot of anomaly scores for both
       baseline and subspace detectors, with vertical lines indicating ground truth anomalies.

    Figures are saved into the `figures/` directory relative to the workspace root.
    """
    figures_dir = Path('figures')
    figures_dir.mkdir(exist_ok=True)
    
    # Plot 1: Metrics Comparison
    results_path = Path('results.csv')
    if results_path.exists():
        try:
            results_df = pd.read_csv(results_path)
            metrics_to_plot = ['AUC_ROC', 'F1_SCORE', 'PRECISION', 'RECALL', 'SPECIFICITY']
            # Filter for available metrics
            available_metrics = [m for m in metrics_to_plot if m in results_df['metric'].values]
            
            if not available_metrics:
                # No data to plot, skip
                pass
            else:
                filtered_df = results_df[results_df['metric'].isin(available_metrics)]
                pivot_data = pd.pivot_table(filtered_df, values='value', index='metric', columns='method', aggfunc='mean')
                
                plt.figure(figsize=(10, 6))
                ax = sns.barplot(data=pivot_data.reset_index(), x='metric', y=pivot_data.columns.tolist(), palette=['#1f77b4', '#ff7f0e'])
                ax.set_xlabel('Metric')
                ax.set_ylabel('Mean Value')
                ax.set_title('Comparison of Metrics: Baseline vs Subspace Methods')
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.savefig(figures_dir / 'metrics_comparison.png', bbox_inches='tight')
                plt.close()
        except Exception as e:
            # Silently fail to generate metrics plot if CSV is malformed
            print(f"Warning: Could not generate metrics comparison plot: {e}")
    
    # Plot 2: Score Distribution
    scores_path = figures_dir / 'scores_for_plots.csv'
    if scores_path.exists():
        try:
            scores_df = pd.read_csv(scores_path)
            gt_anomalies = []
            # Use correct column names from score_exporter.py
            if 'y_true' in scores_df.columns:
                gt_indices = scores_df[scores_df['y_true'] == True].index
                gt_anomalies = list(gt_indices.values)
            
            plt.figure(figsize=(12, 6))
            
            # Determine score columns based on expected output of score_exporter
            base_col = 'base_scores'
            subspace_col = 'subspace_scores'
            
            if base_col in scores_df.columns:
                sns.kdeplot(data=scores_df[[base_col]], fill=True, label='Baseline', alpha=0.3, color='#1f77b4')
            if subspace_col in scores_df.columns:
                sns.kdeplot(data=scores_df[[subspace_col]], fill=True, label='Subspace', alpha=0.3, color='#ff7f0e')
                
            # Mark ground truth locations
            if gt_anomalies:
                plt.axvline(x=np.min(scores_df[base_col]), color='gray', linestyle='--', alpha=0.5)
                plt.axvline(x=np.max(scores_df[base_col]), color='gray', linestyle='--', alpha=0.5)
            
            plt.xlabel('Anomaly Score')
            plt.ylabel('Density')
            plt.title('Anomaly Score Distribution (Baseline vs Subspace)')
            plt.legend()
            plt.tight_layout()
            plt.savefig(figures_dir / 'score_distribution.png', bbox_inches='tight')
            plt.close()
        except Exception as e:
            # Silently fail to generate score plot if CSV is malformed
            print(f"Warning: Could not generate score distribution plot: {e}")