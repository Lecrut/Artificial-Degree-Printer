import csv
from pathlib import Path
import matplotlib.pyplot as plt

def generate_plots(output_dir='.'):
    """
    Generate comparative bar chart for Bio-Signal Anomaly Detection results.
    Uses ONLY standard csv and matplotlib (no pandas/seaborn).
    """
    # Read data from results.csv
    csv_path = Path(output_dir) / 'results.csv'
    if not csv_path.exists():
        raise FileNotFoundError(f"Benchmark results not found at {csv_path}")
    
    methods = []
    f1_scores = []
    precisions = []
    recalls = []
    far_scores = [] # False Alarm Rate
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            methods.append(row['method'])
            f1_scores.append(float(row['f1_score']))
            precisions.append(float(row['precision']))
            recalls.append(float(row['recall']))
            far_scores.append(float(row['false_alarm_rate']))

    # Prepare for plotting
    labels = [m.capitalize() if m != 'baseline' else 'Baseline (Z-Score)' for m in methods]
    x = range(len(methods))
    width = 0.35  

    # Create subplots for F1/Recall vs False Alarm Rate
    fig, ax1 = plt.subplots(figsize=(8, 6))

    # Plot Precision, Recall, F1 on primary axis (ax1)
    color_f1 = '#0284c7' # Blue
    color_prec = '#059669' # Green
    color_rec = '#d97706' # Amber
    
    bar1 = ax1.bar([i - width/2 for i in x], precisions, width, label='Precision', color=color_prec)
    bar2 = ax1.bar(x, f1_scores, width, label='F1-Score', color=color_f1)
    bar3 = ax1.bar([i + width/2 for i in x], recalls, width, label='Recall', color=color_rec)

    # Plot False Alarm Rate on secondary axis (ax2)
    ax2 = ax1.twinx()
    line2 = ax2.plot(x, far_scores, 'k--', marker='o', linewidth=2, markersize=8, label='False Alarm Rate')

    # Formatting
    ax1.set_xlabel('Detection Method', fontsize=12)
    ax1.set_ylabel('Score (0-1)', color=color_f1, fontsize=11)
    ax2.set_ylabel('False Alarm Rate', color='black', fontsize=11)
    
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    
    # Add value labels on bars
    for bar in bar1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                 f'{height:.3f}', ha='center', va='bottom', fontsize=9, color=color_prec)
    for bar in bar2:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                 f'{height:.3f}', ha='center', va='bottom', fontsize=9, color=color_f1)
    for bar in bar3:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                 f'{height:.3f}', ha='center', va='bottom', fontsize=9, color=color_rec)
    
    # Add value labels on line
    for i, v in enumerate(far_scores):
        ax2.text(x[i], v + 0.001, f'{v:.3f}', ha='center', va='bottom', fontsize=9, color='black')

    fig.legend(loc='upper right', bbox_to_anchor=(1.1, 1.1))
    plt.title('Bio-Signal Anomaly Detection: Performance Comparison', fontsize=14)
    
    # Ensure figures directory exists
    fig_dir = Path(output_dir) / 'figures'
    fig_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_p = fig_dir / 'comparison_chart.pdf'
    png_p = fig_dir / 'comparison_chart.png'
    
    # Save figures
    fig.savefig(png_p, dpi=150, bbox_inches='tight')
    fig.savefig(pdf_p, bbox_inches='tight')
    plt.close(fig)
    
    return [str(pdf_p), str(png_p)]