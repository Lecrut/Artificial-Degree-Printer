"""Aggregates and exports raw anomaly scores and ground truth labels for visualization support."""
import numpy as np
import os
from typing import Optional
OUTPUT_DIR: str = 'figures'
OUTPUT_FILENAME: str = 'scores_for_plots.csv'

def export_scores(dataset_y_true: np.ndarray, baseline_scores: np.ndarray, subspace_scores: Optional[np.ndarray]=None) -> None:
    """Save ground truth labels and anomaly scores to a CSV file for downstream visualization.

    The output file is written as `figures/scores_for_plots.csv` (relative to the current working directory).

    Args:
        dataset_y_true: A 1D boolean or integer array of shape (n_samples,) representing the ground truth labels.
        baseline_scores: A 1D float array of shape (n_samples,) containing the anomaly scores from the baseline Z-score detector.
        subspace_scores: An optional 1D float array of shape (n_samples,) containing the anomaly scores from the random subspace ensemble detector.
    """
    import csv
    import os
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if not dataset_y_true.shape[0]:
        return
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        headers = ['sample_id', 'ground_truth', 'baseline_score']
        headers.extend(['subspace_score'] * (subspace_scores is not None and subspace_scores.shape[0] > 0))
        writer.writerow(headers)
        for i in range(dataset_y_true.shape[0]):
            row = [i, int(dataset_y_true[i]), float(baseline_scores[i])]
            if subspace_scores is not None:
                row.extend(subspace_scores[i].tolist())
            writer.writerow(row)
