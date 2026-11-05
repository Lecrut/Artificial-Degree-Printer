import csv
from pathlib import Path
import matplotlib.pyplot as plt

def generate_plots(output_dir='.'):
    fig_dir = Path(output_dir) / 'figures'
    fig_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    rows = []
    with open('results.csv', 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    methods = [r['method'] for r in rows]
    accuracies = [float(r['final_accuracy']) for r in rows]
    resilience = [float(r['straggler_resilience_rate']) for r in rows]
    
    fig, ax1 = plt.subplots(figsize=(8, 5))
    
    # Bar chart for accuracy
    x = range(len(methods))
    bars = ax1.bar(x, accuracies, color=['#94a3b8', '#0284c7'], width=0.6, label='Final Accuracy')
    ax1.set_xlabel('Method')
    ax1.set_ylabel('Final Accuracy', color='#0284c7')
    ax1.set_xticks(x)
    ax1.set_xticklabels([m.capitalize() for m in methods])
    ax1.tick_params(axis='y', labelcolor='#0284c7')
    
    # Add value labels on bars
    for bar, val in zip(bars, accuracies):
        ax1.text(bar.get_x() + bar.get_width() / 2., bar.get_height() + 0.005,
                 f'{val:.4f}', ha='center', va='bottom', fontsize=10)
    
    # Secondary axis for resilience
    ax2 = ax1.twinx()
    ax2.bar(x, resilience, color=['#cbd5e1', '#38bdf8'], width=0.6, alpha=0.4, label='Resilience')
    ax2.set_ylabel('Straggler Resilience Rate', color='#38bdf8')
    ax2.tick_params(axis='y', labelcolor='#38bdf8')
    
    fig.tight_layout()
    
    pdf_p = fig_dir / 'comparison_chart.pdf'
    png_p = fig_dir / 'comparison_chart.png'
    
    fig.savefig(pdf_p)
    fig.savefig(png_p, dpi=150)
    plt.close(fig)
    
    return [str(pdf_p), str(png_p)]
