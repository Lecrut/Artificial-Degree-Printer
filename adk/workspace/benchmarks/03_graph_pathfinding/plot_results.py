import csv
from pathlib import Path
import matplotlib.pyplot as plt

def generate_plots(output_dir='.'):
    fig_dir = Path(output_dir) / 'figures'
    fig_dir.mkdir(parents=True, exist_ok=True)
    pdf_p = fig_dir / 'comparison_chart.pdf'
    png_p = fig_dir / 'comparison_chart.png'
    
    # Read data from CSV
    data = []
    with open('results.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row)
    
    # Prepare data for plotting
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
    
    # Add value labels on bars
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.2f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom')
    
    ax.set_xlabel('Method')
    ax.set_ylabel('Rate')
    ax.set_title('Performance Comparison: Baseline vs Proposed')
    ax.set_xticks(x)
    ax.set_xticklabels(methods)
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    fig.tight_layout()
    fig.savefig(pdf_p)
    fig.savefig(png_p, dpi=150)
    plt.close(fig)
    
    return [str(pdf_p), str(png_p)]
