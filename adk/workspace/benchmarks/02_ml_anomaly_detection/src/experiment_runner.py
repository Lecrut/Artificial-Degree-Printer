"""Module for running the experiment and saving results."""
import csv
from typing import Dict
import numpy as np
from src.config import ANOMALY_RATE, NUM_CHANNELS, NUM_SAMPLES, NOISE_STD, ROBUST_THRESHOLD, RANDOM_STATE, SEEDS, ZSCORE_THRESHOLD
from src.baselines import UnivariateZScoreBaseline
from src.ensemble_detector import RobustEnsembleDetector
from src.synthetic_data import SyntheticDataset

def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Compute Precision, Recall, F1.

    Args:
        y_true: Ground truth boolean array.
        y_pred: Predicted boolean array.

    Returns:
        Dictionary with 'precision', 'recall', 'f1' values.
    """
    tp = int((y_true & y_pred).sum())
    fp = int((~y_true & y_pred).sum())
    fn = int((y_true & ~y_pred).sum())
    precision: float = tp / (tp + fp) if tp + fp > 0 else 0.0
    recall: float = tp / (tp + fn) if tp + fn > 0 else 0.0
    f1: float = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0.0
    return {'precision': precision, 'recall': recall, 'f1': f1}

def run_experiment() -> None:
    """Run the anomaly detection experiment for all seeds and save results to CSV.

    Reads parameters from src.config module-level constants (direct imports).
    Writes 'results.csv' in the workspace root with columns: method, metric, value, seed.
    One row per run per metric per method to preserve seed-level granularity.
    """
    np.random.seed(RANDOM_STATE)
    methods = [('zscore', UnivariateZScoreBaseline), ('ensemble', RobustEnsembleDetector)]
    metrics = ['precision', 'recall', 'f1']
    results_rows = []
    for method_name, DetectorClass in methods:
        for seed in SEEDS:
            dataset = SyntheticDataset(NUM_SAMPLES, NUM_CHANNELS, NOISE_STD, ANOMALY_RATE)
            X, y = dataset.generate(seed=seed)
            split_idx = int(NUM_SAMPLES * 0.8)
            X_train, X_test = (X[:split_idx], X[split_idx:])
            y_train, y_test = (y[:split_idx], y[split_idx:])
            if method_name == 'zscore':
                det = UnivariateZScoreBaseline(threshold=ZSCORE_THRESHOLD)
            else:
                det = RobustEnsembleDetector(threshold=ROBUST_THRESHOLD)
            det.fit(X_train)
            y_pred = det.predict(X_test)
            for metric_name in metrics:
                metric_value = compute_metrics(y_test, y_pred)[metric_name]
                results_rows.append({'method': method_name, 'metric': metric_name, 'value': metric_value, 'seed': seed})
    with open('results.csv', 'w', newline='') as csvfile:
        fieldnames = ['method', 'metric', 'value', 'seed']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results_rows)
