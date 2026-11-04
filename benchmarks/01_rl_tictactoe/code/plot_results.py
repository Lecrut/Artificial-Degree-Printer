import csv
from pathlib import Path
import matplotlib.pyplot as plt

def generate_plots(output_dir='.'):
    fig_dir = Path(output_dir) / 'figures'
    fig_dir.mkdir(parents=True, exist_ok=True)
    
    # Read CSV data
    rows = []
    with open('results.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
            
    if not rows:
        return []

    methods = [r['method'] for r in rows]
    wins = [float(r['win_rate']) for r in rows]
    draws = [float(r['draw_rate']) for r in rows]
    losses = [float(r['loss_rate']) for r in rows]

    x = range(len(methods))
    width = 0.35

    fig, ax = plt.subplots(figsize=(6, 4))
    bars1 = ax.bar([i - width/2 for i in x], wins, width, label='Win Rate', color='#0284c7')
    bars2 = ax.bar([i + width/2 for i in x], draws, width, label='Draw Rate', color='#94a3b8')
    # Plotting losses as stacked or separate? Let's do grouped for clarity as per typical ML plots
    # To keep it simple and zero-dependency robust, let's just compare Win/Draw rates which are key indicators of RL improvement.
    
    ax.set_xlabel('Method')
    ax.set_ylabel('Rate')
    ax.set_title('Tic-Tac-Toe Training Results: Baseline vs Q-Learning Agent')
    ax.set_xticks(list(x))
    ax.set_xticklabels([m.replace('_', ' ').title() for m in methods])
    ax.legend()

    # Save artifacts
    pdf_p = fig_dir / 'comparison_chart.pdf'
    png_p = fig_dir / 'comparison_chart.png'
    
    fig.savefig(pdf_p)
    fig.savefig(png_p, dpi=150)
    plt.close(fig)
    
    return [str(pdf_p), str(png_p)]
