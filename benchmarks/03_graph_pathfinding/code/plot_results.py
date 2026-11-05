import csv
from pathlib import Path
import matplotlib.pyplot as plt

def generate_plots(output_dir='.'):
    fig_dir = Path(output_dir) / 'figures'
    fig_dir.mkdir(parents=True, exist_ok=True)
    pdf_p = fig_dir / 'comparison_chart.pdf'
    png_p = fig_dir / 'comparison_chart.png'
    
    # Read data from results.csv
    baseline_nodes = 0.0
    proposed_nodes = 0.0
    
    with open('results.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['method'] == 'baseline':
                baseline_nodes = float(row['avg_expanded_nodes'])
            elif row['method'] == 'proposed':
                proposed_nodes = float(row['avg_expanded_nodes'])

    # Create plot
    fig, ax = plt.subplots(figsize=(6, 4))
    methods = ['Baseline (Dijkstra)', 'Proposed (Weighted A*)']
    values = [baseline_nodes, proposed_nodes]
    colors = ['#94a3b8', '#0284c7']
    
    ax.bar(methods, values, color=colors)
    ax.set_ylabel('Average Expanded Nodes')
    ax.set_title('Pathfinding Efficiency Comparison')
    ax.tick_params(axis='x', labelsize=10)
    
    # Add value labels on bars
    for i, v in enumerate(values):
        ax.text(i, v + max(values)*0.01, f'{v:.1f}', ha='center', va='bottom')

    fig.tight_layout()
    fig.savefig(pdf_p)
    fig.savefig(png_p, dpi=150)
    plt.close(fig)
    
    return [str(pdf_p), str(png_p)]