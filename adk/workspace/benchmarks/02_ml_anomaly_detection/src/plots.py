"""Module for plotting experiment results."""
import pandas as pd
import matplotlib.pyplot as plt
import os

def plot_results() -> None:
    """Read results.csv and generate F1 score boxplots and confusion matrix.

    Saves figures to the 'figures/' directory.
    """
    import os
    import pandas as pd
    import matplotlib.pyplot as plt
    os.makedirs('figures', exist_ok=True)
    df = pd.read_csv('results.csv')
    f1_data = df[df['metric'] == 'f1'].copy()
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Anomaly Detection Performance: F1-Score by Seed', fontsize=14)
    f1_by_method = f1_data.groupby(['method', 'seed'])['value'].mean().reset_index()
    p = axes[0].boxplot([f1_by_method[f1_by_method.method == m]['value'].values for m in f1_by_method.method.unique()], labels=list(f1_by_method.method.unique()), patch_artist=True)
    axes[0].set_title('F1-Score Boxplots (per seed)')
    axes[0].set_ylabel('F1-Score')
    ensemble_df = f1_data[f1_by_method.method == 'Ensemble'].sort_values(by='seed').reset_index(drop=True)
    n_samples = len(ensemble_df)
    matrix_size = int(n_samples ** 0.5)
    cm_data = ensemble_df[['precision', 'recall']].copy()
    fig.add_subplot(101)
    axes[1].imshow(cm_data.values.T, cmap='YlGnBu', aspect='auto')
    axes[1].set_xticks([])
    axes[1].set_yticks([])
    axes[1].set_title('Precision vs Recall (Ensemble Method)\n(Calculated per seed)')
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    fig.savefig('figures/f1_scores_and_cm_comparison.png', bbox_inches='tight')
