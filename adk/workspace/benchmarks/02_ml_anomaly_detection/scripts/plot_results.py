"""Visualization script for experiment results."""
import pandas as pd
import matplotlib.pyplot as plt

def generate_plots(results_df: pd.DataFrame, output_dir: str) -> None:
    """Generate comparison plots and save to output_dir.

    Creates a bar chart comparing F1-Score precision metrics between the ZScoreBaseline and RobustEnsemble across repetitions.

    Args:
        results_df (pd.DataFrame): DataFrame with columns ['method', 'metric', 'value'] containing experiment results.
        output_dir (str): Directory path where figures will be saved.
    """
    import matplotlib.pyplot as plt
    from scipy import stats
    plt.style.use('seaborn-v0_8-whitegrid')
    f1_data = results_df[(results_df['metric'] == 'f1_score') & results_df['method'].isin(['ZScoreBaseline', 'RobustEnsemble'])].sort_values('method').reset_index(drop=True)
    methods = f1_data['method'].unique().tolist()
    scores = []
    std_devs = []
    n_runs = []
    for method in methods:
        mask = f1_data['method'] == method
        subset = f1_data.loc[mask, 'value']
        scores.append(float(subset.mean()))
        std_devs.append(float(stats.sem(subset)))
        n_runs.append(int(len(subset)))
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(methods, scores, yerr=std_devs, capsize=5, color=['#1f77b4', '#d62728'])
    ax.set_ylabel('F1-Score')
    ax.set_title('Anomaly Detection Performance: ZScoreBaseline vs. RobustEnsemble\n(Comparing multi-feature robust ensemble against static univariate baseline)')
    ax.legend([bars[0], bars[1]], ['ZScoreBaseline', 'RobustEnsemble'], loc='upper right')
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    plot_path = f'{output_dir}/figures/comparison_f1_score.png'
    plt.savefig(plot_path, bbox_inches='tight', dpi=300)
    plt.close()
    return plot_path
