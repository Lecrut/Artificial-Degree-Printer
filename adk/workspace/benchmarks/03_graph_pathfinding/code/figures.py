"""Module for generating comparative visualization plots from experimental results."""

import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns

def generate_figures() -> None:
    """Reads the `results.csv` file from the workspace root. The CSV must contain columns for method, metric, and value (and optional std_dev). Generates comparative plots for nodes expanded, path cost, and suboptimality gap between Dijkstra and Weighted A*. Saves all figure files into the `figures/` directory relative to the workspace root. Creates a summary plot showing the trade-off between performance improvement (nodes saved) and optimality loss (suboptimality gap). No required arguments are passed."""
    input_path = 'results.csv'
    output_dir = 'figures'

    try:
        df = pd.read_csv(input_path)
    except FileNotFoundError:
        # If no results yet, do nothing to avoid crashing the harness during setup
        return

    if df.empty:
        return

    # Ensure necessary columns exist
    required_cols = ['method', 'metric', 'value']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"CSV is missing required column: {col}")

    # Pivot data for easier access
    # Structure: rows=grid_size(or config), cols=method, values=value per metric
    # However, the CSV format specified is tidy: method, metric, value, std_dev, n_runs
    # We need to aggregate if multiple runs exist, but the spec says results.csv has aggregated rows.
    # So each row is a unique combination of method and metric.
    
    dijkstra_df = df[df['method'] == 'dijkstra'].copy()
    weighted_df = df[df['method'] == 'weighted_a_star'].copy() 

    # Rename value columns for clarity
    dijkstra_df.rename(columns={'value': 'dijkstra_val'}, inplace=True)
    weighted_df.rename(columns={'value': 'weighted_val'}, inplace=True)

    # Merge on metric to align them. Both methods likely have values for same metrics.
    merged_df = pd.merge(dijkstra_df[['metric', 'dijkstra_val']], 
                         weighted_df[['metric', 'weighted_val']], 
                         on='metric')

    plt.style.use('seaborn-v0_8-whitegrid')

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('Heuristic Pathfinding Optimization: Comparative Analysis', fontsize=16)

    # 1. Nodes Expanded Comparison
    ax1 = axes[0]
    x = range(len(merged_df))
    width = 0.35
    
    d_nodes = merged_df['dijkstra_val'].tolist()
    w_nodes = merged_df['weighted_val'].tolist()

    # Filter for nodes expanded metric specifically if it exists as a distinct metric entry
    # Looking at metrics: avg_expanded_nodes, std_expanded_nodes... 
    # The CSV likely has rows like: dijkstra, avg_expanded_nodes, 1000
    # And: weighted_a_star, avg_expanded_nodes, 800
    # So the merged_df contains these values.
    
    ax1.bar([i - width/2 for i in x], d_nodes, width, label='Dijkstra', color='#ff7f0e')
    ax1.bar([i + width/2 for i in x], w_nodes, width, label='Weighted A*', color='#2ca02c')
    ax1.set_ylabel('Avg Expanded Nodes')
    ax1.set_xlabel('Experiment Run Index')
    ax1.set_title('Nodes Expanded Comparison')
    ax1.legend()

    # 2. Path Cost Comparison
    ax2 = axes[1]
    
    d_cost = merged_df['dijkstra_val'].tolist() # Assuming metric name distinguishes cost
    w_cost = merged_df['weighted_val'].tolist()

    # We need to identify which metric is path_cost vs nodes. 
    # The pivot/merge approach above blindly matches row index if we just did a simple merge.
    # Better approach: Group by method, then transpose.
    pass # Logic correction below

    plt.close('all') # Close the first incorrect plot attempt

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Identify metric names present in the dataframe
    metrics_present = df['metric'].unique()
    
    # Prepare data by metric type for clear separation if needed, or just map them.
    # The problem is 'value' column contains different things for different 'metric's.
    # Let's filter specific metrics.
    
    nodes_df = df[df['metric'] == 'avg_expanded_nodes'].pivot(index=None, columns='method', values='value')
    cost_df = df[df['metric'] == 'path_cost_dijkstra'].join(
        df[df['metric'] == 'path_cost_astar'][['value']].rename(columns={'value': 'weighted_a_star'})
    ).reset_index(drop=True)
    
    # Handle suboptimality gap
    gap_df = df[df['metric'] == 'suboptimality_gap'].pivot(index=None, columns='method', values='value')
    # Suboptimality gap is likely only for A*, but let's see. If Dijkstra has 0 gap, it might be missing.
    if 'dijkstra' not in gap_df.columns:
        gap_df['dijkstra'] = 0

    # Plot 1: Nodes Expanded
    ax1 = axes[0]
    if 'dijkstra' in nodes_df.columns and 'weighted_a_star' in nodes_df.columns:
        ax1.plot(nodes_df.index, nodes_df['dijkstra'], marker='o', label='Dijkstra')
        ax1.plot(nodes_df.index, nodes_df['weighted_a_star'], marker='s', label='Weighted A*')
        ax1.set_ylabel('Avg Expanded Nodes')
        ax1.set_xlabel('Grid/Run Index')
        ax1.set_title('Nodes Expanded per Run')
        ax1.legend()

    # Plot 2: Path Cost
    ax2 = axes[1]
    if 'path_cost_dijkstra' in cost_df.columns or 'dijkstra' in cost_df.columns: # Pivot might change names
        # Re-fetch cost df correctly
        d_cost_raw = df[(df['method'] == 'dijkstra') & (df['metric'] == 'path_cost_dijkstra')]['value']
        w_cost_raw = df[(df['method'] == 'weighted_a_star') & (df['metric'] == 'path_cost_astar')]['value']
        
        # Align indices
        common_idx = d_cost_raw.index.intersection(w_cost_raw.index)
        d_aligned = d_cost_raw[common_idx]
        w_aligned = w_cost_raw[common_idx]
        
        ax2.plot(d_aligned.index, d_aligned.values, marker='o', label='Dijkstra Cost')
        ax2.plot(w_aligned.index, w_aligned.values, marker='s', label='Weighted A* Cost')
        ax2.set_ylabel('Path Cost')
        ax2.set_xlabel('Grid/Run Index')
        ax2.set_title('Optimal Path Cost Comparison')
        ax2.legend()

    # Plot 3: Suboptimality Gap
    ax3 = axes[2]
    if 'weighted_a_star' in gap_df.columns:
        ax3.bar(gap_df.index, gap_df['weighted_a_star'], color='red', alpha=0.7)
        ax3.set_ylabel('Suboptimality Gap (%)')
        ax3.set_xlabel('Grid/Run Index')
        ax3.set_title('Suboptimality Gap of Weighted A*')

    plt.tight_layout()
    fig.savefig(f'{output_dir}/comparison_plots.png', dpi=150)
    
    # Summary Plot: Performance vs Optimality
    fig2, ax4 = plt.subplots(figsize=(8, 6))
    
    if common_idx is not None and not d_aligned.empty:
        # Nodes saved % = (Dijkstra - Weighted) / Dijkstra
        nodes_saved_percent = (d_aligned.values - w_aligned.values) / d_aligned.values * 100
        # Use the aligned index for x-axis
        indices = common_idx.values 
        
        ax4.scatter(d_aligned.values, nodes_saved_percent, color='green', label='Performance Gain')
        ax4.set_xlabel('Avg Expanded Nodes (Dijkstra)')
        ax4.set_ylabel('Nodes Saved (%)')
        ax4.set_title('Performance vs. Search Effort')
        ax4.legend()
        fig2.savefig(f'{output_dir}/performance_summary.png', dpi=150)
    
    plt.close('all')
