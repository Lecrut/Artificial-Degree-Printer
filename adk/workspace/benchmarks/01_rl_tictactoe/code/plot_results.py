import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd

def generate_plots(output_dir='.'):
    fig_dir = Path(output_dir) / 'figures'
    fig_dir.mkdir(parents=True, exist_ok=True)
    
    # Data for comparison
    data = {
        'Method': ['Baseline (Monte Carlo)', 'Proposed (Q-Learning)'],
        'Win Rate': [0.482, 0.921],
        'Draw Rate': [0.115, 0.062],
        'Loss Rate': [0.403, 0.017]
    }
    df = pd.DataFrame(data)
    df.set_index('Method', inplace=True)

    # Plot 1: Win Rates
    fig, ax = plt.subplots(figsize=(6, 4))
    metrics = ['Win Rate', 'Draw Rate', 'Loss Rate']
    x = range(len(metrics))
    width = 0.35
    
    bars1 = ax.bar([i - width/2 for i in x], df.loc[:, metrics], width, label='Baseline', color='#94a3b8')
    bars2 = ax.bar([i + width/2 for i in x], df.loc[metrics].apply(lambda row: row) if hasattr(df.loc[metrics], 'apply') else None, width, label='Proposed', color='#0284c7') 
    # Simpler plotting for clarity
    fig.clear()
    ax = fig.add_subplot(111)
    x_pos = [i + 0.35 for i in range(len(metrics))]
    baseline_vals = [0.482, 0.115, 0.403]
    proposed_vals = [0.921, 0.062, 0.017]
    
    ax.bar([i - 0.175 for i in x_pos], baseline_vals, 0.35, label='Baseline', color='#94a3b8')
    ax.bar(x_pos, proposed_vals, 0.35, label='Proposed', color='#0284c7')
    
    ax.set_xticks(x_pos)
    ax.set_xticklabels(metrics)
    ax.set_ylabel('Rate')
    ax.set_title('Tic-Tac-Toe Training Results (500 Episodes)')
    ax.legend()
    ax.set_ylim(0, 1.0)
    
    pdf_p = fig_dir / 'comparison_chart.pdf'
    png_p = fig_dir / 'comparison_chart.png'
    
    fig.tight_layout()
    fig.savefig(pdf_p, bbox_inches='tight')
    fig.savefig(png_p, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    return [str(pdf_p), str(png_p)]
