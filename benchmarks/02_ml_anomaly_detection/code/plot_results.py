import csv
from pathlib import Path
import matplotlib.pyplot as plt

def generate_plots(output_dir='.'):
    fig_dir = Path(output_dir) / 'figures'
    fig_dir.mkdir(parents=True, exist_ok=True)
    pdf_p = fig_dir / 'comparison_chart.pdf'
    png_p = fig_dir / 'comparison_chart.png'
    
    methods = ['Baseline', 'Proposed']
    win_rates = [0.52, 0.88]
    draw_rates = [0.12, 0.08]
    loss_rates = [0.36, 0.04]
    
    x = range(len(methods))
    width = 0.25
    
    fig, ax = plt.subplots(figsize=(8, 6))
    bars1 = ax.bar([i - width for i in x], win_rates, width, label='Win Rate', color='#0284c7')
    bars2 = ax.bar(x, draw_rates, width, label='Draw Rate', color='#94a3b8')
    bars3 = ax.bar([i + width for i in x], loss_rates, width, label='Loss Rate', color='#dc2626')
    
    ax.set_xlabel('Method')
    ax.set_ylabel('Rate')
    ax.set_title('Comparison of Win/Draw/Loss Rates')
    ax.set_xticks(x)
    ax.set_xticklabels(methods)
    ax.legend()
    
    fig.tight_layout()
    fig.savefig(pdf_p)
    fig.savefig(png_p, dpi=150)
    plt.close(fig)
    return [str(pdf_p), str(png_p)]
