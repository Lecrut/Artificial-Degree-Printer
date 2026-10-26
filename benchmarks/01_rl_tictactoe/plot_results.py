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
    with open('results.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    methods = [row['method'] for row in data]
    win_rates = [float(row['win_rate']) for row in data]
    draw_rates = [float(row['draw_rate']) for row in data]
    loss_rates = [float(row['loss_rate']) for row in data]
    
    # Create bar chart
    x = range(len(methods))
    width = 0.25
    
    fig, ax = plt.subplots(figsize=(8, 6))
    bars1 = ax.bar([i - width for i in x], win_rates, width, label='Win Rate', color='#4CAF50')
    bars2 = ax.bar(x, draw_rates, width, label='Draw Rate', color='#FFC107')
    bars3 = ax.bar([i + width for i in x], loss_rates, width, label='Loss Rate', color='#F44336')
    
    ax.set_xlabel('Methods')
    ax.set_ylabel('Rate')
    ax.set_title('Comparison of Win, Draw, and Loss Rates')
    ax.set_xticks(x)
    ax.set_xticklabels(methods)
    ax.legend()
    
    fig.tight_layout()
    fig.savefig(pdf_p)
    fig.savefig(png_p, dpi=150)
    plt.close(fig)
    
    return [str(pdf_p), str(png_p)]
