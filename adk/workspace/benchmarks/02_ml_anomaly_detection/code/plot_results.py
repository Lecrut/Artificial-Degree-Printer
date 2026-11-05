import csv
from pathlib import Path
import matplotlib.pyplot as plt

def generate_plots(output_dir='.'):
    fig_dir = Path(output_dir) / 'figures'
    fig_dir.mkdir(parents=True, exist_ok=True)
    pdf_p = fig_dir / 'comparison_chart.pdf'
    png_p = fig_dir / 'comparison_chart.png'
    
    # Read data
    with open('results.csv', 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    baseline_f1 = float(rows[0]['baseline_f1_score'])
    proposed_f1 = float(rows[0]['proposed_f1_score'])
    
    fig, ax = plt.subplots(figsize=(6, 4))
    methods = ['Baseline', 'Proposed']
    scores = [baseline_f1, proposed_f1]
    colors = ['#94a3b8', '#0284c7']
    
    bars = ax.bar(methods, scores, color=colors, width=0.5)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}',
                ha='center', va='bottom')
    
    ax.set_ylabel('F1 Score')
    ax.set_title('Anomaly Detection Performance Comparison')
    ax.set_ylim(0, 1.1)
    fig.tight_layout()
    
    fig.savefig(pdf_p)
    fig.savefig(png_p, dpi=150)
    plt.close(fig)
    return [str(pdf_p), str(png_p)]
