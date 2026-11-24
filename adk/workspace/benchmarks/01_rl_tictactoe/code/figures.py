"""Generate academic plots from experimental results stored in CSV files."""
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
from typing import Optional
FIGURE_DIR: str = 'figures'
RESULTS_FILE: str = 'results.csv'
TRAINING_LOG_FILE: str = 'training_log.csv'

def generate_plots() -> None:
    """Reads results.csv and training_log.csv to generate learning curves and performance comparison plots.

    This function loads aggregated experimental results from `results.csv` (tidy format with columns
    `method`, `metric`, `value`, optional `std_dev`) and intermediate training dynamics from 
    `training_log.csv` (columns: `step`, `epoch`, `win_rate`, `draw_rate`, `loss_rate`, etc.).

    It generates the following figures saved to `figures/`:
    1. `training_dynamics.png`: Line plot of win/draw/loss rates over training epochs/steps.
    2. `final_performance.png`: Bar chart comparing final metrics (win_rate, draw_rate, 
       loss_rate, avg_game_length) between the Q-Learning agent and the Random baseline.

    If the input CSV files are missing or empty, this function does not raise an error but 
    skips plot generation for the respective data source.
    """
    from pathlib import Path
    import pandas as pd
    ROOT_DIR = Path().resolve()
    RESULTS_PATH = ROOT_DIR / RESULTS_FILE
    LOG_PATH = ROOT_DIR / TRAINING_LOG_FILE
    FIGURES_DIR = Path(FIGURE_DIR)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    win_data: pd.Series | None = None
    draw_data: pd.Series | None = None
    loss_data: pd.Series | None = None
    if LOG_PATH.exists() and LOG_PATH.stat().st_size > 0:
        try:
            df_log = pd.read_csv(LOG_PATH)
            cols_win = ['win_rate', 'Win_rate']
            cols_draw = ['draw_rate', 'Draw_rate']
            cols_loss = ['loss_rate', 'Loss_rate']
            win_data = df_log[cols_win].apply(pd.to_numeric, errors='coerce').iloc[:, 0]
            draw_data = df_log[cols_draw].apply(pd.to_numeric, errors='coerce').iloc[:, 0]
            loss_data = df_log[cols_loss].apply(pd.to_numeric, errors='coerce').iloc[:, 0]
        except Exception:
            pass
    if win_data is not None and len(win_data) > 0:
        try:
            import matplotlib.pyplot as plt
            df_train = pd.DataFrame({'epoch': list(range(len(win_data))), 'win_rate': win_data, 'draw_rate': draw_data if draw_data is not None else [0.0] * len(win_data), 'loss_rate': loss_data if loss_data is not None else [0.0] * len(win_data)})
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), tight_layout=True)
            ax1.plot(df_train['epoch'], df_train['win_rate'], label='Win Rate', color='green')
            ax1.set_ylabel('Rate')
            ax1.set_title('Training Dynamics: Win Rate Over Epochs')
            ax1.grid(True, alpha=0.3)
            ax2.plot(df_train['epoch'], df_train['draw_rate'], label='Draw Rate', color='yellow')
            ax2.plot(df_train['epoch'], df_train['loss_rate'], label='Loss Rate', color='red')
            ax2.set_xlabel('Epoch')
            ax2.set_ylabel('Rate')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            fig.savefig(FIGURES_DIR / 'training_dynamics.png', bbox_inches='tight')
        except Exception:
            pass
    q_data: pd.DataFrame | None = None
    random_data: pd.DataFrame | None = None
    if RESULTS_PATH.exists() and RESULTS_PATH.stat().st_size > 0:
        try:
            df_results = pd.read_csv(RESULTS_PATH)
            q_methods = [m for m in df_results['method'].unique() if 'Q-Learning' in str(m) or 'q-learning' in str(m)]
            random_methods = [m for m in df_results['method'].unique() if 'Random' in str(m) or 'random' in str(m)]
            q_dfs = df_results[df_results['method'].isin(q_methods)].groupby('method').agg({'win_rate': 'mean', 'draw_rate': 'mean', 'loss_rate': 'mean', 'avg_game_length': 'mean'}).reset_index()
            random_dfs = df_results[df_results['method'].isin(random_methods)].groupby('method').agg({'win_rate': 'mean', 'draw_rate': 'mean', 'loss_rate': 'mean', 'avg_game_length': 'mean'}).reset_index()
            final_df = pd.concat([q_dfs, random_dfs], ignore_index=True)
            if len(final_df) > 1:
                fig_comp, ax = plt.subplots(figsize=(8, 6))
                metrics_to_plot = ['win_rate', 'draw_rate', 'loss_rate', 'avg_game_length']
                for col in metrics_to_plot:
                    if col in final_df.columns:
                        ax.bar(final_df['method'], final_df[col], alpha=0.7, edgecolor='black')
                ax.set_ylabel('Value')
                ax.set_xlabel('Method')
                ax.set_title('Final Performance Comparison: Q-Learning vs Random Baseline')
                ax.grid(axis='y', alpha=0.3)
                plt.tight_layout()
                fig_comp.savefig(FIGURES_DIR / 'final_performance.png', bbox_inches='tight')
            else:
                print('Warning: Only one method group found. Skipping comparative bar chart.')
        except Exception:
            pass
