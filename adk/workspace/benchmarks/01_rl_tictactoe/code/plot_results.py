import csv
from pathlib import Path
import matplotlib.pyplot as plt

def generate_plots(output_dir='.'):
    fig_dir = Path(output_dir) / 'figures'
    fig_dir.mkdir(parents=True, exist_ok=True)
    pdf_p = fig_dir / 'comparison_chart.pdf'
    png_p = fig_dir / 'comparison_chart.png'
    
    # Read data
    rows = []
    with open('results.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    methods = [r['method'] for r in rows]
    win_rates = [float(r['win_rate']) for r in rows]
    draw_rates = [float(r['draw_rate']) for r in rows]
    loss_rates = [float(r['loss_rate']) for r in rows]
    
    x = range(len(methods))
    width = 0.25
    
    fig, ax = plt.subplots(figsize=(8, 5))
    
    ax.bar([i + width for i in x], win_rates, width, label='Win Rate', color='#0284c7')
    ax.bar(x, draw_rates, width, label='Draw Rate', color='#94a3b8')
    ax.bar([i - width for i in x], loss_rates, width, label='Loss Rate', color='#ef4444')
    
    ax.set_ylabel('Rate')
    ax.set_title('Tic-Tac-Toe Agent Performance Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(methods)
    ax.legend()
    
    # Set y limit slightly above 1.0 to fit stacked bars visually if needed, or just max value
    ax.set_ylim(0, 1.05)
    
    fig.tight_layout()
    fig.savefig(pdf_p)
    fig.savefig(png_p, dpi=150)
    plt.close(fig)
    
    return [str(pdf_p), str(png_p)]