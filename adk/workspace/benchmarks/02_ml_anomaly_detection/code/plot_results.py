import csv
from pathlib import Path
import matplotlib.pyplot as plt

def generate_plots(output_dir='.'):
    fig_dir = Path(output_dir) / 'figures'
    fig_dir.mkdir(parents=True, exist_ok=True)
    pdf_p = fig_dir / 'comparison_chart.pdf'
    png_p = fig_dir / 'comparison_chart.png'
    
    # Read data
    metrics = ['precision', 'recall', 'f1_score', 'false_alarm_rate']
    x = [0, 1]
    baseline_data = []
    proposed_data = []
    
    with open('results.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['method'] == 'baseline':
                baseline_data = [float(row[m]) for m in metrics]
            elif row['method'] == 'proposed':
                proposed_data = [float(row[m]) for m in metrics]
    
    width = 0.35
    fig, ax = plt.subplots(figsize=(8, 5))
    bars1 = ax.bar([i - width/2 for i in x], baseline_data, width, label='Baseline (Z-Score)', color='#94a3b8')
    bars2 = ax.bar([i + width/2 for i in x], proposed_data, width, label='Proposed (Mahalanobis Ensemble)', color='#0284c7')
    
    ax.set_ylabel('Score / Rate')
    ax.set_title('Anomaly Detection Performance Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics, rotation=15)
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    fig.tight_layout()
    fig.savefig(pdf_p)
    fig.savefig(png_p, dpi=150)
    plt.close(fig)
    return [str(pdf_p), str(png_p)]