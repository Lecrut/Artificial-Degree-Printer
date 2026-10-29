import csv
from pathlib import Path
import matplotlib.pyplot as plt

def generate_plots(output_dir='.'):
    fig_dir = Path(output_dir) / 'figures'
    fig_dir.mkdir(parents=True, exist_ok=True)
    pdf_p = fig_dir / 'comparison_chart.pdf'
    png_p = fig_dir / 'comparison_chart.png'
    
    # Read data from results.csv
    data = {}
    csv_path = Path(output_dir) / 'results.csv'
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            method = row['method']
            data[method] = {
                'win_rate': float(row['win_rate']),
                'draw_rate': float(row['draw_rate']),
                'loss_rate': float(row['loss_rate'])
            }
    
    # Prepare bar chart
    methods = ['baseline', 'proposed']
    win_rates = [data[m]['win_rate'] for m in methods]
    draw_rates = [data[m]['draw_rate'] for m in methods]
    loss_rates = [data[m]['loss_rate'] for m in methods]
    
    x = range(len(methods))
    width = 0.25
    
    fig, ax = plt.subplots(figsize=(6, 4))
    bars1 = ax.bar([i - width for i in x], win_rates, width, label='Win Rate', color='#0284c7')
    bars2 = ax.bar(x, draw_rates, width, label='Draw Rate', color='#94a3b8')
    bars3 = ax.bar([i + width for i in x], loss_rates, width, label='Loss Rate', color='#dc2626')
    
    ax.set_xlabel('Method')
    ax.set_ylabel('Rate')
    ax.set_title('Win/Draw/Loss Rates Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(methods)
    ax.legend()
    
    fig.savefig(pdf_p)
    fig.savefig(png_p, dpi=150)
    plt.close(fig)
    return [str(pdf_p), str(png_p)]
