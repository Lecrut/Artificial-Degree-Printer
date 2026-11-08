from __future__ import annotations

import csv
import os
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.multioutput import MultiOutputClassifier
from sklearn.preprocessing import StandardScaler

from config import ANOMALY_RATIO, ENSEMBLE_TREES, N_SAMPLES, Z_THRESHOLD


def generate_biosignal_dataset(
    n_samples: int = N_SAMPLES,
    anomaly_ratio: float = ANOMALY_RATIO,
    seed: int = 42
) -> tuple[NDArray[np.float64], NDArray[np.int64]]:
    """
    Generate synthetic bio-signal telemetry data with injected anomalies.

    This function simulates a univariate sensor stream (e.g., ECG or PPG) by
    combining deterministic low-frequency trends with stochastic high-frequency noise.
    Anomalies are injected by scaling the signal amplitude significantly above the
    normal distribution bounds defined by the `Z_THRESHOLD`.

    Algorithmic Steps:
        1. Initialize random state for determinism.
        2. Generate base sine wave (physiological rhythm).
        3. Overlay Gaussian noise (sensor noise).
        4. Calculate anomaly indices based on `anomaly_ratio`.
        5. Inject anomalies by scaling signal values at selected indices.

    Time Complexity: O(n_samples)
    Space Complexity: O(n_samples)

    Args:
        n_samples: Total number of telemetry samples to generate.
        anomaly_ratio: Fraction of samples to be classified as anomalous.
        seed: Random seed for reproducibility.

    Returns:
        signal: Array of shape (n_samples,) containing the sensor readings.
        labels: Binary array of shape (n_samples,) where 1 indicates an anomaly.
    """
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 10, n_samples)
    base_signal = np.sin(2 * np.pi * t)
    noise = rng.normal(0, 0.1, n_samples)
    signal = base_signal + noise
    n_anomalies: int = int(n_samples * anomaly_ratio)
    anomaly_indices = rng.choice(n_samples, size=n_anomalies, replace=False)
    labels = np.zeros(n_samples, dtype=np.int64)
    anomaly_magnitude: float = float(ENSEMBLE_TREES)
    signal[anomaly_indices] *= anomaly_magnitude
    labels[anomaly_indices] = 1
    return (signal, labels)


def train_and_evaluate(
    csv_out_path: str | Path = 'results.csv',
    seed: int = 42
) -> None:
    """
    Compare a static Univariate Z-Score baseline against an Adaptive Robust Mahalanobis-Ensemble detector.

    This function generates data, computes features, and runs two distinct detection algorithms:
    1. **Baseline**: Static univariate thresholding using `Z_THRESHOLD`.
    2. **Proposed**: A multi-feature ensemble approach combining feature scaling, isolation trees,
       and robust covariance estimation to detect complex telemetry anomalies.

    The results (precision, recall, f1_score, false_alarm_rate) are written to `csv_out_path`.

    Args:
        csv_out_path: File path to save the comparative evaluation results.
        seed: Random seed for reproducibility of data generation and model training.
    """
    signal, labels = generate_biosignal_dataset(
        n_samples=N_SAMPLES,
        anomaly_ratio=ANOMALY_RATIO,
        seed=seed
    )
    window_size: int = 10
    n_feat: int = 3
    features = np.empty((len(signal), n_feat))
    features[:, 0] = signal
    rolling_mean = np.convolve(signal, np.ones(window_size) / window_size, mode='same')
    rolling_std = np.zeros_like(signal)
    for i in range(len(signal)):
        start = max(0, i - window_size // 2)
        end = min(len(signal), i + window_size // 2 + 1)
        rolling_std[i] = np.std(signal[start:end])
    features[:, 1] = rolling_mean
    features[:, 2] = rolling_std
    mu_signal: float = float(np.mean(signal))
    std_signal: float = float(np.std(signal))
    if std_signal == 0:
        std_signal = 1.0
    z_scores = np.abs((signal - mu_signal) / std_signal)
    baseline_labels = (z_scores > Z_THRESHOLD).astype(np.int64)
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    iso_forest = IsolationForest(
        n_estimators=ENSEMBLE_TREES,
        contamination=float(ANOMALY_RATIO),
        random_state=seed
    )
    iso_labels_raw = iso_forest.fit_predict(features_scaled)
    iso_binary = (iso_labels_raw == -1).astype(np.int64)
    med_features = np.median(features, axis=0)
    mad_features = np.median(np.abs(features - med_features), axis=0)
    mad_features[mad_features == 0] = 1e-09
    diff = features - med_features
    distances = np.sqrt(np.sum((diff / mad_features) ** 2, axis=1))
    mah_threshold: float = Z_THRESHOLD * 2.0
    mah_binary = (distances > mah_threshold).astype(np.int64)
    proposed_labels = iso_binary & mah_binary

    def calculate_metrics(
        y_true: NDArray[np.int64],
        y_pred: NDArray[np.int64]
    ) -> dict[str, float]:
        """
        Calculate precision, recall, f1_score, and false_alarm_rate.

        Args:
            y_true: Ground truth binary labels.
            y_pred: Predicted binary labels.

        Returns:
            Dictionary of metrics.
        """
        prec = float(precision_score(y_true, y_pred, zero_division=0))
        rec = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))
        tn = np.sum((y_true == 0) & (y_pred == 0))
        fp = np.sum((y_true == 0) & (y_pred == 1))
        far = float(fp / (fp + tn)) if fp + tn > 0 else 0.0
        return {'precision': prec, 'recall': rec, 'f1_score': f1, 'false_alarm_rate': far}

    baseline_metrics = calculate_metrics(labels, baseline_labels)
    proposed_metrics = calculate_metrics(labels, proposed_labels)

    header = ['method', 'precision', 'recall', 'f1_score', 'false_alarm_rate']
    csv_path = Path(csv_out_path)
    os.makedirs(csv_path.parent, exist_ok=True)

    with open(csv_out_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerow(['baseline'] + list(baseline_metrics.values()))
        writer.writerow(['proposed'] + list(proposed_metrics.values()))

    print(f'Results saved to {csv_out_path}')
