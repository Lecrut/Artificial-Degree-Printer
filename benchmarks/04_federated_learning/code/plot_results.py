import csv
from pathlib import Path
import matplotlib.pyplot as plt

def generate_plots(output_dir='.'):
    # Ensure output directory exists
    fig_dir = Path(output_dir) / 'figures'
    fig_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_p = fig_dir / 'comparison_chart.pdf'
    png_p = fig_dir / 'comparison_chart.png'
    
    # Read CSV data manually without pandas
    with open('results.csv', 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    methods = [r['method'] for r in rows]
    accuracies = [float(r['final_accuracy']) for r in rows]
    latencies = [float(r['latency_ms']) for r in rows]
    stragglers = [float(r['straggler_resilience_rate']) for r in rows]

    # Dual-axis chart configuration
    fig, ax1 = plt.subplots(figsize=(8, 5))
    
    x = range(len(methods))
    bar_width = 0.35
    
    # Plot Accuracy (Primary Axis - Bars)
    color_acc = '#2c3e50'
    ax1.bar(x, accuracies, width=bar_width, label='Final Accuracy', color=color_acc, alpha=0.8)
    ax1.set_ylabel('Final Accuracy (Accuracy)', color=color_acc)
    ax1.tick_params(axis='y', labelcolor=color_acc)
    
    # Plot Straggler Resilience (Secondary Axis - Line)
    ax2 = ax1.twinx()
    color_strag = '#c0392b'
    line_pos = [pos + bar_width/2 for pos in x]
    ax2.plot(line_pos, stragglers, marker='o', color=color_strag, label='Straggler Resilience Rate')
    ax2.set_ylabel('Straggler Resilience Rate (Rate)', color=color_strag)
    ax2.tick_params(axis='y', labelcolor=color_strag)
    
    # Formatting
    ax1.set_title('Federated Learning: Performance & Robustness Comparison', fontsize=14, fontweight='bold')
    ax1.set_xticks([pos + bar_width/2 for pos in x])
    ax1.set_xticklabels([m.capitalize() for m in methods])
    
    # Combine legends
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='lower right')
    
    plt.tight_layout()
    
    # Save outputs
    fig.savefig(pdf_p, format='pdf', bbox_inches='tight')
    fig.savefig(png_p, format='png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    return [str(pdf_p), str(png_p)]
