"""Reads experiment results and training history to generate static plots."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import pandas as pd
FIGURES_DIR: str = 'figures'

def plot_results() -> None:
    """Read `results.csv` and `training_history.csv`, generate and save plots.

    Reads two files from the current working directory (workspace root):
    1. `results.csv`: Contains final aggregated metrics (`method`, `metric`, `value`).
       Used for the payoff comparison bar chart (win/draw/loss rates).
    2. `training_history.csv`: Contains training progress (`episode`, `reward` or `avg_reward`).
       Used for the learning curve visualization.

    Generates two figures and saves them into the `figures/` directory:
    1. `q_learning_curve.png`: Line plot of average reward over episodes.
    2. `payoff_comparison.png`: Bar chart comparing win/draw/loss rates between methods.

    Ensures the `figures/` directory exists before saving.
    """
    base_dir: str = os.getcwd()
    results_path: str = os.path.join(base_dir, 'results.csv')
    history_path: str = os.path.join(base_dir, 'training_history.csv')
    os.makedirs(FIGURES_DIR, exist_ok=True)
    if not os.path.isfile(results_path):
        return
    df_results: pd.DataFrame = pd.read_csv(results_path)
    methods = sorted(df_results['method'].unique())
    fig_payoff, ax_payoff = plt.subplots(figsize=(8, 6))
    x_indices: list[int] = []
    labels: list[str] = []
    bar_width = 0.35
    index = 0.0
    for method in methods:
        wins = df_results.loc[(df_results['method'] == method) & (df_results['metric'] == 'win_rate'), 'value']
        draws = df_results.loc[(df_results['method'] == method) & (df_results['metric'] == 'draw_rate'), 'value']
        losses = df_results.loc[(df_results['method'] == method) & (df_results['metric'] == 'loss_rate'), 'value']
        val_win: float = wins.values[0] if len(wins) > 0 else 0.0
        val_draw: float = draws.values[0] if len(draws) > 0 else 0.0
        val_loss: float = losses.values[0] if len(losses) > 0 else 0.0
        x_indices.append(index)
        labels.append(method.replace('_', ' ').title())
        ax_payoff.bar(index, val_win, bar_width, color='green', label='Win')
        ax_payoff.bar(index, val_draw, bar_width, bottom=val_win, color='gray', label='Draw (Offset: 1)')
        ax_payoff.bar(index, val_loss, bar_width, bottom=val_win + val_draw, color='red', label='Loss (Offset: 2)')
        index += bar_width + 0.1
    ax_payoff.set_xticks([i + bar_width / 2 for i in x_indices])
    ax_payoff.set_xticklabels(labels)
    ax_payoff.set_ylabel('Rate')
    ax_payoff.set_title('Payoff Comparison (Win/Draw/Loss)')
    handles, legend_labels = ax_payoff.get_legend_handles_labels()
    if legend_labels:
        unique_handles: list = []
        for h_item, lbl in zip(handles, legend_labels):
            if lbl not in [item_lbl for _, item_lbl in unique_handles]:
                unique_handles.append((h_item, lbl))
        ax_payoff.legend([h for h, _ in unique_handles], [lbl for _, lbl in unique_handles], title=None)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, 'payoff_comparison.png'), bbox_inches='tight')
    plt.close(fig_payoff)
    if os.path.isfile(history_path):
        df_history = pd.read_csv(history_path)
        if len(df_history) > 0:
            fig_curve, ax_curve = plt.subplots(figsize=(10, 6))
            reward_col: str | None = 'avg_reward' if 'avg_reward' in df_history.columns else 'reward' if 'reward' in df_history.columns else None
            if reward_col is not None:
                df_history_sorted = df_history.sort_values(by='episode')
                episodes: list[float] = df_history_sorted['episode'].values.tolist()
                rewards: list[float] = df_history_sorted[reward_col].values.tolist()
                ax_curve.plot(episodes, rewards, marker='o', linestyle='-', color='#b22232', label='Avg Reward')
                ax_curve.set_title('Average Reward Over Episodes (Q-Learning)')
                ax_curve.set_xlabel('Episode')
                ax_curve.set_ylabel('Average Reward')
                ax_curve.legend(loc='lower right')
                ax_curve.grid(True, linestyle='--', alpha=0.6)
                plt.tight_layout()
                plt.savefig(os.path.join(FIGURES_DIR, 'q_learning_curve.png'), bbox_inches='tight')
                plt.close(fig_curve)
