"""Module for visualizing experiment results."""
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import sys
sys.path.insert(0, str(Path.cwd()))

# Apply style after imports to avoid NameError issues with local scope
matplotlib = __import__('matplotlib')
mpl_backend = 'Agg'
mpl.use(mpl_backend)
plt_style = matplotlib.style
plt_style.use('ggplot')
sns_style_path = __import__('seaborn').style
sns_style_path.set_style("whitegrid")

"""Read results.csv and generate figures in figures/ directory.

Generates:
1. convergence.png: Convergence of average reward over episodes (win_rate_q).
2. comparison.png: Comparison of win rates between Q-Learning and Random player.

The function reads the 'results.csv' file from the current workspace root.
"""

def plot_results() -> None:
    """Read results.csv and generate figures in figures/ directory."""
    # Define output paths
    output_dir = Path("figures")
    output_dir.mkdir(exist_ok=True)
    convergence_plot_path = output_dir / "convergence.png"
    comparison_plot_path = output_dir / "comparison.png"
    
    # Load data from results.csv
    try:
        df = pd.read_csv("results.csv")
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Experiment not yet run: {Path.cwd()}/results.csv does not exist. "
            "Please run the experiment first."
        )
    
    # Check for required columns
    required_metrics = ["method", "metric", "value", "std_dev"]
    missing_cols = set(required_metrics) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns in results.csv: {missing_cols}")
    
    # --- Figure 1: Convergence Plot ---
    # We aggregate by method to get the learning curve
    df_agg = df.groupby("method").agg({"value": "mean", "std_dev": "first"}).reset_index()
    
    plt.figure(figsize=(8, 6))
    
    if "Q-Learning" in df_agg["method"].values:
        q_idx = df_agg[df_agg["method"] == "Q-Learning"].index[0]
        plt.plot(df_agg.iloc[q_idx]["value"], marker='o', label='Q-Learning', linestyle='-')
    
    if "Random" in df_agg["method"].values:
        rand_idx = df_agg[df_agg["method"] == "Random"].index[0]
        plt.plot(df_agg.iloc[rand_idx]["value"], marker='s', label='Random Baseline', linestyle='--')
    
    # Add baseline at value=0.5 (target win rate for 3x3 zero-sum)
    plt.axhline(y=0.5, color='gray', linestyle=':', alpha=0.7, label='Target Win Rate (50%)')
    plt.xlabel('Episodes')
    plt.ylabel('Average Win Rate')
    plt.title('Convergence of Q-Learning vs Random Baseline')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    
    plt.tight_layout()
    convergence_plot_path.parent.mkdir(exist_ok=True)
    convergence_plot_path = output_dir / "convergence.png"
    plt.savefig(convergence_plot_path)
    plt.close()
    
    # --- Figure 2: Final Comparison Chart ---
    final_metrics_df = df[df["metric"] == "win_rate_q"].groupby("method")['value'].mean().reset_index()
    final_metrics_df.columns = ['Method', 'Final Win Rate']
    final_metrics_df.rename(columns={'Method': 'method', 'Final Win Rate': 'value'}, inplace=True)
    
    comparison_df = pd.DataFrame(
        {
            'method': final_metrics_df["method"],
            "metric": "win_rate",
            "value": final_metrics_df["value"]
        }
    )
    
    bars = plt.bar(comparison_df["method"], comparison_df["value"], color=['blue', 'red'], edgecolor='black')
    plt.xlabel('Agent Method')
    plt.ylabel('Average Win Rate (%)')
    plt.title('Performance Comparison: Q-Learning vs Random Player')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                 f'{height:.3f}',
                 ha='center', va='bottom' if height > 0 else 'top', fontsize=10)
    
    # Annotate target
    plt.axhline(y=0.5, color='k', linestyle='--', alpha=0.4, label='Target (50%)')
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.3)
    
    plt.tight_layout()
    comparison_plot_path.parent.mkdir(exist_ok=True)
    comparison_plot_path = output_dir / "comparison.png"
    plt.savefig(comparison_plot_path)
    plt.close()


def plot_reward_convergence() -> None:
    """Generate convergence plot based on reward metric."""
    df = pd.read_csv("results.csv")
    
    if "avg_reward_q" not in df.columns:
        raise ValueError("Metric 'avg_reward_q' not found in results.csv.")
    
    df_agg = df.groupby("method").agg({"avg_reward_q": "mean", "std_dev": "first"}).reset_index()
    columns_to_plot = ["value"]
    
    plt.figure(figsize=(8, 6))
    if "Q-Learning" in df_agg["method"].values:
        q_idx = df_agg[df_agg["method"] == "Q-Learning"].index[0]
        plt.plot(df_agg.iloc[q_idx][columns_to_plot], marker='o', label='Q-Learning', linestyle='-')
    
    if "Random" in df_agg["method"].values:
        rand_idx = df_agg[df_agg["method"] == "Random"].index[0]
        plt.plot(df_agg.iloc[rand_idx][columns_to_plot], marker='s', label='Random Baseline', linestyle='--')
    
    plt.xlabel('Episodes')
    plt.ylabel('Average Reward')
    plt.title('Convergence of Q-Learning vs Random Baseline (Reward)')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    
    output_dir = Path("figures")
    output_dir.mkdir(exist_ok=True)
    plt.savefig(output_dir / "reward_convergence.png")
    plt.close()

# Define global metric names for easy access if needed by other modules
METRIC_NAMES = ["win_rate_q", "win_rate_random", "avg_reward_q"]