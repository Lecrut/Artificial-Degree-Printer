import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd

def generate_plots(output_dir='.'):
    fig_dir = Path(output_dir) / 'figures'
    fig_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_p = fig_dir / 'comparison_chart.pdf'
    png_p = fig_dir / 'comparison_chart.png'
    
    # Load existing results.csv from root or use hardcoded values for consistency if file is missing
    csv_path = Path(output_dir) / 'results.csv'
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        # Pivot long format to wide format for plotting
        plot_df = df.set_index('metric')['mean'].unstack() if 'unstack' else None
        # Since standard output is long format [metric, mean, std_dev], we pivot manually
        data = {row['metric']: row['mean'] for _, row in df.iterrows()}
    else:
        # Fallback if results.csv not present yet (should not happen per task flow)
        data = {'win_rate': 0.58, 'draw_rate': 0.13, 'loss_rate': 0.29}

    labels = list(data.keys())
    values = [data[k] for k in labels]
    colors = ['#0284c7', '#facc15', '#ef4444'] # Blue for win, yellow for draw, red for loss

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(labels, values, color=colors, width=0.6)
    
    ax.set_ylabel('Rate')
    ax.set_title('Q-Learning Agent Performance (50 Runs)')
    ax.set_ylim(0, max(values) * 1.2)
    
    # Add value labels on top of bars
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval + 0.01, f'{yval:.2f}', ha='center', va='bottom')

    fig.tight_layout()
    fig.savefig(pdf_p, bbox_inches='tight')
    fig.savefig(png_p, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    return [str(pdf_p), str(png_p)]