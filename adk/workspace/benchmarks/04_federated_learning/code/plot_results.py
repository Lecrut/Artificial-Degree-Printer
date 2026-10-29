import csv
from pathlib import Path
import matplotlib.pyplot as plt

def generate_plots(output_dir='.'):
    fig_dir = Path(output_dir) / 'figures'
    fig_dir.mkdir(parents=True, exist_ok=True)
    pdf_p = fig_dir / 'comparison_chart.pdf'
    png_p = fig_dir / 'comparison_chart.png'
    
    # Read data from results.csv
    data = []
    with open('results.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row)
    
    methods = [row['method'] for row in data]
    win_rates = [float(row['win_rate']) for row in data]
    
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(methods, win_rates, color=['#94a3b8', '#0284c7'])
    ax.set_ylabel('Win Rate')
    ax.set_title('Performance Comparison: Baseline vs Proposed')
    ax.set_ylim(0, 1)
    
    # Add value labels on bars
    for bar, rate in zip(bars, win_rates):
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                f'{rate:.2f}',
                ha='center', va='bottom')
    
    fig.savefig(pdf_p)
    fig.savefig(png_p, dpi=150)
    plt.close(fig)
    return [str(pdf_p), str(png_p)]
