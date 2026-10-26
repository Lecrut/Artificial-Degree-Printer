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
    with open('results.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row)
    
    # Extract values
    baseline_win = float(data[0]['win_rate'])
    proposed_win = float(data[1]['win_rate'])
    
    # Plotting
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(['Baseline', 'Proposed'], [baseline_win, proposed_win], color=['#94a3b8', '#0284c7'])
    ax.set_ylabel('Win Rate')
    ax.set_title('Comparison of Win Rates: Baseline vs Proposed')
    ax.set_ylim(0, 1)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom')
    
    fig.savefig(pdf_p)
    fig.savefig(png_p, dpi=150)
    plt.close(fig)
    return [str(pdf_p), str(png_p)]
