import csv
from pathlib import Path
import matplotlib.pyplot as plt

def generate_plots(output_dir='.'):
    fig_dir = Path(output_dir) / 'figures'
    fig_dir.mkdir(parents=True, exist_ok=True)
    pdf_p = fig_dir / 'comparison_chart.pdf'
    png_p = fig_dir / 'comparison_chart.png'
    
    # Read data using csv module as mandated
    rows = []
    with open('results.csv', mode='r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
            
    methods = [row['method'] for row in rows]
    win_rates = [float(row['win_rate']) for row in rows]
    draw_rates = [float(row['draw_rate']) for row in rows]
    
    fig, ax = plt.subplots(figsize=(8, 6))
    x = range(len(methods))
    width = 0.35
    
    bars1 = ax.bar([i - width/2 for i in x], win_rates, width, label='Win Rate', color='#0284c7')
    bars2 = ax.bar([i + width/2 for i in x], draw_rates, width, label='Draw Rate', color='#94a3b8')
    
    ax.set_ylabel('Rate')
    ax.set_title('Tic-Tac-Toe Agent Performance: Baseline vs Q-Learning')
    ax.set_xticks(list(x))
    ax.set_xticklabels([m.replace('_', '\n') for m in methods]) # Nice formatting
    ax.legend()
    
    fig.tight_layout()
    fig.savefig(pdf_p)
    fig.savefig(png_p, dpi=150)
    plt.close(fig)
    
    return [str(pdf_p), str(png_p)]