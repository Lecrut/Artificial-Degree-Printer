"""
Plotting utilities for generating figures.
Generates architecture diagrams inline (Mermaid) instead of referencing non-existent files.
"""
import matplotlib.pyplot as plt
import os
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
ARCH_DIAGRAM = '\ngraph TD;\n    subgraph Agent { \n        direction TB\n        QLearner[Q-Learning Agent];\n        RandomAgent[Random Agent Baseline]; \n    }\n    subgraph Env { \n        TicTacToeEnv[Tic-Tac-Toe Environment];\n    }\n    QLearner --> TicTacToeEnv; \n    RandomAgent --> TicTacToeEnv;\n'

def generate_diagram_text() -> str:
    """
    Generate the Mermaid diagram string for the architecture.
    Returns: A Mermaid sequence defining the environment, agent, and baseline interaction.
    """
    return ARCH_DIAGRAM

def plot_learning_curve(results: List[Dict], output_path: str, columns_to_plot: Optional[List[str]]=None) -> None:
    """
    Plot the learning curve of Q-Learning against a random baseline.

    Args:
        results (List[Dict]): List of episodes with 'epoch', 'reward', and 'agent' keys.
        output_path (str): Path to save the plot as an image file.
        columns_to_plot (Optional[List[str]]): Specific column names to aggregate (defaults to ['reward'] for both agents).
    """
    out_dir = Path(output_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    if columns_to_plot is None:
        cols_to_aggregate = ['reward']
    else:
        cols_to_aggregate = columns_to_plot
    df_results = pd.DataFrame(results)
    if 'epoch' not in df_results.columns or 'agent' not in df_results.columns:
        raise ValueError("Results must contain 'epoch' and 'agent' columns.")
    summary_stats = df_results.groupby(['epoch', 'agent'])[cols_to_aggregate].mean()
    plot_data = summary_stats.unpivot('long')
    color_map = {'Q-Learning': '#1f77b4', 'Random Agent': '#ff7f0e'}
    legend_labels = {'Q-Learning': 'Q-Learning Agent (Learning)', 'Random Agent': 'Random Baseline'}
    fig, ax = plt.subplots(figsize=(10, 6))
    lines = []
    for agent_name in ['Q-Learning', 'Random Agent']:
        subset = plot_data[plot_data['agent'] == agent_name]
        ax.plot(subset['epoch'], subset['value'], marker='o', color=color_map[agent_name], label=legend_labels[agent_name])
        lines.append(ax.lines[-1])
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Average Reward per Episode')
    ax.set_title('Learning Curve: Q-Learning vs Random Baseline')
    ax.legend(lines, legend_labels)
    ax.grid(True, alpha=0.3)
    output_file = str(output_path)
    fig.savefig(output_file, bbox_inches='tight', dpi=300)
    plt.close(fig)
