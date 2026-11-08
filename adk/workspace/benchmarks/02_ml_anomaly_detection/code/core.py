"""Core logic for Bio-Signal & Telemetry Anomaly Detection.

This module provides synthetic data generation for biomedical telemetry streams
and implements a comparative evaluation pipeline. The pipeline contrasts a
static univariate Z-score baseline against a multi-feature Adaptive Robust
Mahalanobis-Ensemble detector.
"""
from __future__ import annotations
import os
import csv
from dataclasses import dataclass
from typing import Dict, Tuple
import numpy as np
import pandas as pd
from config import ANOMALY_RATIO, ENSEMBLE_TREES, N_SAMPLES, Z_THRESHOLD

@dataclass(frozen=True)
class AnomalyMetrics:
    """Container for standard anomaly detection evaluation metrics.
    
    Attributes:
        precision: Ratio of correctly identified anomalies to total predicted anomalies.
        recall: Ratio of correctly identified anomalies to total actual anomalies.
        f1_score: Harmonic mean of precision and recall.
        false_alarm_rate: Ratio of healthy samples incorrectly flagged as anomalous.
    """
    precision: float
    recall: float
    f1_score: float
    false_alarm_rate: float

def generate_biosignal_dataset(n_samples: int=N_SAMPLES, anomaly_ratio: float=ANOMALY_RATIO, seed: int=42) -> Tuple[np.ndarray, np.ndarray]:
    """Generate a synthetic multi-feature bio-signal stream with injected anomalies.

    The dataset consists of correlated physiological signals (e.g., heart rate variability,
    respiratory rate, temperature) contaminated with Gaussian noise. A subset of samples
    is marked as anomalous by introducing distribution shifts (mean/magnitude).

    Args:
        n_samples: Total number of time-steps in the synthetic stream.
        anomaly_ratio: Proportion of samples to label as anomalies (0.0 to 1.0).
        seed: Deterministic random seed for reproducibility.

    Returns:
        A tuple containing:
            - X: Array of shape (n_samples, n_features) with synthetic bio-signal features.
            - y: Binary ground truth array of shape (n_samples,), 1 if anomaly, 0 otherwise.
    """
    rng = np.random.default_rng(seed)
    n_features: int = 4
    mean_normal: np.ndarray = np.zeros(n_features)
    cov_normal: np.ndarray = np.diag([1.0, 0.5, 0.8, 0.2])
    X_normal: np.ndarray = rng.multivariate_normal(mean_normal, cov_normal, size=n_samples)
    n_anomalies: int = int(n_samples * anomaly_ratio)
    y: np.ndarray = np.zeros(n_samples, dtype=int)
    n_anomalies = min(n_anomalies, n_samples)
    anomaly_indices: np.ndarray = rng.choice(n_samples, size=n_anomalies, replace=False)
    X_anomaly: np.ndarray = X_normal[anomaly_indices].copy()
    shift_magnitude: float = 3.5
    shifts: np.ndarray = rng.uniform(-1, 1, size=n_features) * shift_magnitude
    X_anomaly += shifts
    X_anomaly += rng.normal(0, 2.0, size=X_anomaly.shape)
    X: np.ndarray = X_normal.copy()
    X[anomaly_indices] = X_anomaly
    y[anomaly_indices] = 1
    return (X, y)

def _evaluate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> AnomalyMetrics:
    """Compute precision, recall, F1-score, and false alarm rate.

    Args:
        y_true: Ground truth binary labels.
        y_pred: Predicted binary labels.

    Returns:
        AnomalyMetrics instance containing computed scores.
    """
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    precision: float = tp / (tp + fp) if tp + fp > 0 else 0.0
    recall: float = tp / (tp + fn) if tp + fn > 0 else 0.0
    f1_score: float = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0.0
    false_alarm_rate: float = fp / (fp + tn) if fp + tn > 0 else 0.0
    return AnomalyMetrics(precision=precision, recall=recall, f1_score=f1_score, false_alarm_rate=false_alarm_rate)

def train_and_evaluate(csv_out_path: str='results.csv', seed: int=42) -> Dict[str, Dict[str, float]]:
    """Execute comparative evaluation against baseline and proposed detectors.

    Generates synthetic bio-signals using `generate_biosignal_dataset`, applies
    both the static Z-score baseline and the adaptive robust Mahalanobis-ensemble
    detector, and saves the results to a CSV file.

    The comparison highlights:
    1. Baseline: Univariate Z-Score per feature with threshold Z_THRESHOLD.
    2. Proposed: Adaptive Robust Mahalanobis Distance estimated via an Ensemble
       of covariance matrices (simulating robustness to outliers).

    Args:
        csv_out_path: Destination path for the empirical benchmark metrics CSV.
        seed: Deterministic RNG seed (default: 42).

    Returns:
        Dictionary mapping model names ('baseline', 'proposed') to their metric dictionaries.
    """
    X, y_true = generate_biosignal_dataset(n_samples=N_SAMPLES, anomaly_ratio=ANOMALY_RATIO, seed=seed)
    n_features: int = X.shape[1]
    results: Dict[str, Dict[str, float]] = {}
    feat_means: np.ndarray = np.mean(X, axis=0)
    feat_stds: np.ndarray = np.std(X, axis=0) + 1e-08
    z_scores: np.ndarray = np.abs((X - feat_means) / feat_stds)
    y_pred_baseline: np.ndarray = (z_scores.max(axis=1) > Z_THRESHOLD).astype(int)
    metrics_baseline: AnomalyMetrics = _evaluate_metrics(y_true, y_pred_baseline)
    results['baseline'] = {'precision': metrics_baseline.precision, 'recall': metrics_baseline.recall, 'f1_score': metrics_baseline.f1_score, 'false_alarm_rate': metrics_baseline.false_alarm_rate}
    ensemble_distances: list[np.ndarray] = []
    n_bootstraps: int = ENSEMBLE_TREES
    rng_ens: np.random.Generator = np.random.default_rng(seed + 1)
    sample_size: int = N_SAMPLES // 2
    for _ in range(n_bootstraps):
        indices = rng_ens.choice(N_SAMPLES, size=sample_size, replace=False)
        X_subset: np.ndarray = X[indices]
        mu_sub: np.ndarray = np.mean(X_subset, axis=0)
        cov_sub: np.ndarray = np.cov(X_subset, rowvar=False)
        reg_cov: np.ndarray = cov_sub + 0.001 * np.eye(n_features)
        try:
            inv_cov_sub: np.ndarray = np.linalg.inv(reg_cov)
        except np.linalg.LinAlgError:
            inv_cov_sub = np.eye(n_features)
        diffs: np.ndarray = X - mu_sub
        left_side: np.ndarray = diffs @ inv_cov_sub
        dist_sq: np.ndarray = np.sum(left_side * diffs, axis=1)
        ensemble_distances.append(dist_sq)
    avg_mahalanobis_dist: np.ndarray = np.mean(ensemble_distances, axis=0)
    threshold_percentile: float = np.percentile(avg_mahalanobis_dist, 100 * (1 - ANOMALY_RATIO))
    y_pred_proposed: np.ndarray = (avg_mahalanobis_dist > threshold_percentile).astype(int)
    metrics_proposed: AnomalyMetrics = _evaluate_metrics(y_true, y_pred_proposed)
    results['proposed'] = {'precision': metrics_proposed.precision, 'recall': metrics_proposed.recall, 'f1_score': metrics_proposed.f1_score, 'false_alarm_rate': metrics_proposed.false_alarm_rate}
    dir_name = os.path.dirname(csv_out_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    records = [{'method': 'baseline', **results['baseline']}, {'method': 'proposed', **results['proposed']}]
    df = pd.DataFrame(records)
    df.to_csv(csv_out_path, index=False)
    return results

def generate_comparison_plot(csv_path: str='results.csv', out_path: str='figures/comparison_chart.png') -> None:
    """Generate comparison chart from evaluation results.

    Reads the output CSV and plots precision/recall/F1 for baseline vs proposed methods.
    Saves the figure to the specified output path.

    Args:
        csv_path: Path to the results CSV file.
        out_path: Destination path for the generated plot.
    """
    import matplotlib.pyplot as plt
    df = pd.read_csv(csv_path)
    methods = df['method']
    metrics = ['precision', 'recall', 'f1_score']
    x = np.arange(len(methods))
    width = 0.25
    fig, ax = plt.subplots(figsize=(8, 6))
    for i, metric in enumerate(metrics):
        values = df[metric].values
        ax.bar(x + i * width, values, width, label=metric)
    ax.set_xlabel('Method')
    ax.set_ylabel('Score')
    ax.set_title('Anomaly Detection Performance Comparison')
    ax.set_xticks(x + width)
    ax.set_xticklabels([m.capitalize() for m in methods])
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
