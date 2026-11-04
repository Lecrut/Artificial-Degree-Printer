import csv
from pathlib import Path
import matplotlib.pyplot as plt

def generate_plots(output_dir='.'):
    fig_dir = Path(output_dir) / 'figures'
    fig_dir.mkdir(parents=True, exist_ok=True)
    
    # Read data
    csv_path = Path(output_dir) / 'results.csv'
    methods = []
    speeds = []
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            methods.append(row['method'])
            # Using speedup_factor as the primary metric for visualization
            # baseline is 1.0, proposed is >1.0 (or <1.0 depending on definition, here 2.35 implies factor)
            speeds.append(float(row['speedup_factor']))
    
    fig, ax = plt.subplots(figsize=(6, 4))
    
    # Colors: Baseline gray, Proposed blue
    colors = ['#94a3b8', '#0284c7']
    
    bars = ax.bar(methods, speeds, color=colors, edgecolor='black')
    
    ax.set_ylabel('Speedup Factor (relative to Baseline)')
    ax.set_title('Pathfinding Algorithm Performance Comparison')
    ax.set_ylim(0, max(speeds) * 1.2)
    
    # Add value labels on top of bars
    for bar, speed in zip(bars, speeds):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{speed:.2f}',
                ha='center', va='bottom')
    
    plt.tight_layout()
    
    pdf_p = fig_dir / 'comparison_chart.pdf'
    png_p = fig_dir / 'comparison_chart.png'
    
    fig.savefig(pdf_p, format='pdf')
    fig.savefig(png_p, dpi=150)
    plt.close(fig)
    
    return [str(pdf_p), str(png_p)]