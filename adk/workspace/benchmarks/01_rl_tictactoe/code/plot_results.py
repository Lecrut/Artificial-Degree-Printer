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
    wins = [float(r['win_rate']) for r in rows]
    draws = [float(r['draw_rate']) for r in rows]
    losses = [float(r['loss_rate']) for r in rows]
    
    x = range(len(methods))
    width = 0.25
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    ax.bar([i - width for i in x], wins, width, label='Win Rate', color='#10b981')
    ax.bar(x, draws, width, label='Draw Rate', color='#f59e0b')
    ax.bar([i + width for i in x], losses, width, label='Loss Rate', color='#ef4444')
    
    ax.set_ylabel('Rate')
    ax.set_title('Tic-Tac-Toe Agent Performance Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(methods)
    ax.legend()
    
    # Grid
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    
    fig.tight_layout()
    fig.savefig(pdf_p, format='pdf')
    fig.savefig(png_p, dpi=150)
    plt.close(fig)
    
    return [str(pdf_p), str(png_p)]
