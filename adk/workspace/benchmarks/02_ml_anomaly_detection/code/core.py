"""Core logic for Bio-Signal Anomaly Detection.

This module implements two primary detectors for synthetic bio-signal telemetry:
1. **Baseline**: A univariate static Z-score detector.
2. **Proposed**: A multi-feature Adaptive Robust Mahalanobis-Ensemble detector.

The evaluation pipeline generates deterministic synthetic data, applies both detectors,
and outputs comparative metrics (Precision, Recall, F1-Score, False Alarm Rate) to CSV.

Mathematical Formulation for Proposed Method:
    For a feature vector $x \\in \\mathbb{R}^d$, the Mahalanobis distance is defined as:
    $$D_M(x) = \\sqrt{(x - \\mu)^T \\Sigma^{-1} (x - \\mu)}$$
    where $\\mu$ is the robust location estimator (median) and $\\Sigma$ is the robust
    covariance matrix estimated via the Minimum Covariance Determinant (MCD).
"""
import os
from typing import Tuple, Dict, Any, List
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.covariance import MinCovDet
from sklearn.metrics import precision_score, recall_score, f1_score

def generate_biosignal_dataset(n_samples: int, anomaly_ratio: float, seed: int=42) -> Tuple[np.ndarray, np.ndarray]:
    """Generate synthetic bio-signal telemetry data with injected anomalies.

    Args:
        n_samples: Total number of samples to generate.
        anomaly_ratio: Fraction of samples that will be anomalous.
        seed: Random seed for reproducibility.

    Returns:
        features: NumPy array of shape (n_samples, d) containing multi-feature data.
        labels: NumPy array of shape (n_samples,) with 0 (normal) or 1 (anomaly).
    """
    rng = np.random.default_rng(seed)
    n_anomalies = int(n_samples * anomaly_ratio)
    n_features = 4
    mean_normal = np.array([75.0, 98.0, 16.0, 120.0])
    cov_normal = np.diag([4.0 ** 2, 1.5 ** 2, 3.0 ** 2, 10.0 ** 2])
    features_normal = rng.multivariate_normal(mean_normal, cov_normal, n_samples - n_anomalies)
    labels_normal = np.zeros(n_samples - n_anomalies, dtype=int)
    anomaly_range = 15.0
    features_anomalies = rng.uniform(low=mean_normal - anomaly_range * 3, high=mean_normal + anomaly_range * 3, size=(n_anomalies, n_features))
    labels_anomalies = np.ones(n_anomalies, dtype=int)
    features = np.vstack([features_normal, features_anomalies])
    labels = np.hstack([labels_normal, labels_anomalies])
    indices = rng.permutation(n_samples)
    features = features[indices]
    labels = labels[indices]
    return (features, labels)

def train_and_evaluate(csv_out_path: str, seed: int=42) -> pd.DataFrame:
    """Compare Baseline Z-Score vs. Adaptive Robust Mahalanobis-Ensemble detector.

    Generates synthetic bio-signal data, runs both detectors, computes metrics
    including f1_score and false_alarm_rate, and saves results to CSV.

    Args:
        csv_out_path: File path to save the results CSV.
        seed: Random seed for reproducibility.

    Returns:
        metrics_df: DataFrame containing comparison metrics for both methods.
            Columns: method, precision, recall, f1_score, false_alarm_rate.
    """
    from config import N_SAMPLES, ANOMALY_RATIO, Z_THRESHOLD, ENSEMBLE_TREES
    features, labels_true = generate_biosignal_dataset(N_SAMPLES, ANOMALY_RATIO, seed)
    metrics_rows = []
    means = np.mean(features, axis=0)
    stds = np.std(features, axis=0)
    stds[stds == 0] = 1.0
    z_scores = np.abs((features - means) / stds)
    predictions_baseline = (np.max(z_scores, axis=1) > Z_THRESHOLD).astype(int)
    baseline_metrics = _calculate_metrics(labels_true, predictions_baseline)
    baseline_row = {'method': 'baseline', **baseline_metrics}
    metrics_rows.append(baseline_row)
    mcd = MinCovDet(random_state=seed, support_fraction=1.0)
    mcd.fit(features)
    robust_location = mcd.location_
    robust_precision = mcd.precisions_
    diff = features - robust_location
    mahalanobis_distances = np.sqrt(np.sum(diff @ robust_precision * diff, axis=1))
    iso_forest = IsolationForest(n_estimators=ENSEMBLE_TREES, contamination=float(ANOMALY_RATIO), random_state=seed)
    iso_predictions_raw = iso_forest.fit_predict(features)
    predictions_iso = (iso_predictions_raw == -1).astype(int)
    maha_threshold = np.percentile(mahalanobis_distances, 100 * (1 - ANOMALY_RATIO / 2))
    predictions_maha = (mahalanobis_distances > maha_threshold).astype(int)
    predictions_proposed = np.logical_or(predictions_maha, predictions_iso).astype(int)
    proposed_metrics = _calculate_metrics(labels_true, predictions_proposed)
    proposed_row = {'method': 'proposed', **proposed_metrics}
    metrics_rows.append(proposed_row)
    metrics_df = pd.DataFrame(metrics_rows, columns=['method', 'precision', 'recall', 'f1_score', 'false_alarm_rate'])
    out_dir = os.path.dirname(csv_out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    metrics_df.to_csv(csv_out_path, index=False)
    return metrics_df

def _calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculate Precision, Recall, F1-Score, and False Alarm Rate.

    Args:
        y_true: Ground truth labels (0=normal, 1=anomaly).
        y_pred: Predicted labels (0=normal, 1=anomaly).

    Returns:
        Dictionary of metric values containing precision, recall, f1_score,
        and false_alarm_rate.
    """
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    neg_actual_count = np.sum(y_true == 0)
    if neg_actual_count > 0:
        fp_count = np.sum((y_pred == 1) & (y_true == 0))
        far = float(fp_count) / neg_actual_count
    else:
        far = 0.0
    return {'precision': precision, 'recall': recall, 'f1_score': f1, 'false_alarm_rate': far}
