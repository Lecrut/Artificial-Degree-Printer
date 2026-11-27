"""Module for reading results from the experiment and generating static plots for the thesis."""

import os
from typing import List, Tuple

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

RESULTS_PATH: str = "results.csv"
FIGURES_DIR: str = "figures"


def generate_plots() -> None:
    """Reads `results.csv` from the workspace root, generates plots for convergence and comparison metrics, and saves them into `figures/`. Creates the `figures/` directory if it does not exist. Handles missing data or invalid CSV formats gracefully without crashing."""
    # Ensure output directory exists
    os.makedirs(FIGURES_DIR, exist_ok=True)

    try:
        df: pd.DataFrame = pd.read_csv(RESULTS_PATH)
    except FileNotFoundError:
        print(f"Warning: {RESULTS_PATH} not found. Cannot generate plots.")
        return
    except pd.errors.EmptyDataError:
        print("Warning: results.csv is empty. Cannot generate plots.")
        return

    if 'method' not in df.columns or 'metric' not in df.columns or 'value' not in df.columns:
        print("Warning: results.csv does not contain required columns ('method', 'metric', 'value').")
        return

    methods: List[str] = df['method'].unique().tolist()
    metrics: List[str] = df['metric'].unique().tolist()

    # Identify metrics specific to the agent for convergence analysis if applicable.
    # Usually, 'avg_episode_reward' is a time-series or aggregated result. 
    # Here results.csv is tidy: method, metric, value. If it's aggregated, we plot bar charts.
    # If it were step-by-step, structure would differ (e.g., episode column). 
    # Given the spec implies aggregation (mean, std_dev), we treat these as summary statistics.

    # 1. Plot Win Rates for Comparison
    win_metrics: List[str] = [m for m in metrics if 'win_rate' in m]
    draw_metrics: List[str] = [m for m in metrics if 'draw_rate' in m]

    if win_metrics:
        plot_win_draw_rates(df, win_metrics, draw_metrics)

    # 2. Plot Agent Performance Metrics (if available) vs Baseline or just absolute values
    agent_metrics: List[str] = [m for m in metrics if 'agent_' in m]
    if agent_metrics:
        plot_agent_metrics(df, agent_metrics)


def plot_win_draw_rates(df: pd.DataFrame, win_metrics: List[str], draw_metrics: List[str]) -> None:
    """Plots win and draw rates for agents/baselines as bar charts."""
    if not df.empty:
        fig, axes = plt.subplots(1, 2, figsize=(12, 6))
        
        # Win Rates
        wins_data: pd.DataFrame = df[df['metric'].isin(win_metrics)][['method', 'value']]
        if not wins_data.empty:
            ax1: plt.Axes = axes[0]
            ax1.bar(wins_data['method'], wins_data['value'], color=['skyblue', 'lightcoral'])
            ax1.set_title('Win Rates Comparison')
            ax1.set_xlabel('Agent Type')
            ax1.set_ylabel('Win Rate')

        # Draw Rates
        draws_data: pd.DataFrame = df[df['metric'].isin(draw_metrics)][['method', 'value']]
        if not draws_data.empty:
            ax2: plt.Axes = axes[1]
            ax2.bar(draws_data['method'], draws_data['value'], color=['silver', 'lightgray'])
            ax2.set_title('Draw Rates Comparison')
            ax2.set_xlabel('Agent Type')
            ax2.set_ylabel('Draw Rate')
        
        plt.tight_layout()
        plt.savefig(os.path.join(FIGURES_DIR, "win_draw_rates.png"))
        plt.close(fig)


def plot_agent_metrics(df: pd.DataFrame, agent_metrics: List[str]) -> None:
    """Plots aggregated metrics for the learning agent."""
    if not df.empty:
        agents_data: pd.DataFrame = df[df['metric'].isin(agent_metrics)][['metric', 'value']]
        if not agents_data.empty:
            fig: plt.Figure
            ax: plt.Axes
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # Map metric codes to readable names for plotting
            labels: List[str] = []
            values: List[float] = []
            for _, row in agents_data.iterrows():
                m: str = row['metric']
                v: float = row['value']
                label: str = m.replace('_', ' ').title()
                labels.append(label)
                values.append(v)

            ax.bar(labels, values, color='teal')
            ax.set_title('Agent Performance Metrics (Aggregated)')
            ax.set_xlabel('Metric')
            ax.set_ylabel('Value')
            
            plt.tight_layout()
            plt.savefig(os.path.join(FIGURES_DIR, "agent_metrics.png"))
            plt.close(fig)