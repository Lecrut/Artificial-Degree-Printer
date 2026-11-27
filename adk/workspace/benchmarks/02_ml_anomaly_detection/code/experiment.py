"""Runs the full experiment loop over multiple repetitions for anomaly detection evaluation using synthetic data, comparing baseline and proposed detectors via AUC-ROC and F1 score metrics."""
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, roc_auc_score
from data_generator import generate_dataset
from baseline_zscore import ZScoreDetector
from method_random_subspace import RandomSubspaceDetector
N_REPETITIONS: int = 10
DURATION: int = 1000
N_CHANNELS: int = 5
ANOMALY_RATE: float = 0.02
NOISE_STD: float = 0.1
WINDOW_SIZE: int = 50
N_SUBSPACES: int = 10
SUBSPACE_DIM: int = 3

def run_experiment() -> None:
    """Executes the complete experiment loop for robust anomaly detection comparison and writes results to CSV.

    For each of N_REPETITIONS repetitions:
    1. Creates a deterministic `rng` using `np.random.default_rng(repetition + 42)`.
    2. Calls `generate_dataset(n_channels=N_CHANNELS, duration=DURATION, anomaly_rate=ANOMALY_RATE, noise_std=NOISE_STD, rng=rng)` to obtain synthetic telemetry data and ground truth labels.
    3. Initializes the baseline `ZScoreDetector` with `WINDOW_SIZE`. Calls `predict(data)` which returns a continuous numpy array of shape (duration,) representing the maximum absolute Z-score across all channels for each time step.
    4. Computes binary predictions for the baseline using a fixed threshold of 3.0 on these Z-scores (anomaly if max_Z > 3.0). Computes AUC-ROC using the continuous Z-scores against the ground truth labels.
    5. Initializes `RandomSubspaceDetector` with `N_SUBSPACES` and `SUBSPACE_DIM`. Calls `fit(data)` to train on the telemetry data, then `predict(data)` to obtain a continuous anomaly score array of shape (duration,).
    6. Computes binary predictions for the Random Subspace detector using a fixed rule-based threshold: `mean(scores) + 2 * std(scores)`. Anomaly if score > threshold. Computes F1 score using these binary predictions against ground truth.
    7. Aggregates `auc_roc` and `f1_score` across repetitions into a pandas DataFrame with columns: `method`, `metric`, `value`, `std_dev`, `n_runs`. The `method` column contains 'zscore' and 'random_subspace'. The `metric` column contains 'auc_roc' and 'f1_score'.
    8. Writes the DataFrame to 'results.csv' in the current working directory.

    Edge cases:
    - If a metric cannot be computed (e.g., only one class present in predictions), it is omitted or recorded as NaN/0 depending on sklearn defaults.
    - Fixed thresholds ensure consistent interface usage and avoid oracle cheating."""
    all_results: list[dict[str, str | float]] = []
    for rep_idx in range(N_REPETITIONS):
        rng: np.random.Generator = np.random.default_rng(rep_idx + 42)
        data: np.ndarray
        anomaly_mask: np.ndarray
        data, anomaly_mask = generate_dataset(n_channels=N_CHANNELS, duration=DURATION, anomaly_rate=ANOMALY_RATE, noise_std=NOISE_STD, rng=rng)
        if not anomaly_mask.any():
            continue
        zscore_detector: ZScoreDetector = ZScoreDetector(window_size=WINDOW_SIZE)
        zscore_pred_bool: np.ndarray
        max_z_scores: np.ndarray
        zscore_pred_bool, max_z_scores = zscore_detector.predict(data)
        try:
            auc_roc_z: float = roc_auc_score(anomaly_mask, max_z_scores)
        except ValueError:
            auc_roc_z = 0.0
        f1_z: float = 0.0
        if anomaly_mask.sum() > 0 and zscore_pred_bool.sum() > 0:
            try:
                f1_z = f1_score(anomaly_mask, zscore_pred_bool)
            except ValueError:
                f1_z = 0.0
        all_results.append({'method': 'zscore', 'metric': 'auc_roc', 'value': auc_roc_z})
        all_results.append({'method': 'zscore', 'metric': 'f1_score', 'value': f1_z})
        rsub_detector: RandomSubspaceDetector = RandomSubspaceDetector(n_subspaces=N_SUBSPACES, subspace_dim=SUBSPACE_DIM)
        rsub_detector.fit(data)
        rsub_scores: np.ndarray = rsub_detector.predict(data)
        k: float = 2.0
        mean_score: float = np.mean(rsub_scores)
        std_score: float = np.std(rsub_scores)
        if std_score > 1e-08:
            threshold_val: float = mean_score + k * std_score
            rsub_pred_binary: np.ndarray = np.array(rsub_scores > threshold_val, dtype=bool)
        else:
            rsub_pred_binary = np.zeros(DURATION, dtype=bool)
        try:
            auc_roc_rs: float = roc_auc_score(anomaly_mask, rsub_scores)
        except ValueError:
            auc_roc_rs = 0.0
        f1_rs: float = 0.0
        if anomaly_mask.sum() > 0 and rsub_pred_binary.sum() > 0:
            try:
                f1_rs = f1_score(anomaly_mask, rsub_pred_binary)
            except ValueError:
                f1_rs = 0.0
        all_results.append({'method': 'random_subspace', 'metric': 'auc_roc', 'value': auc_roc_rs})
        all_results.append({'method': 'random_subspace', 'metric': 'f1_score', 'value': f1_rs})
    df: pd.DataFrame = pd.DataFrame(all_results)
    if not df.empty:
        grouped: pd.DataFrame = df.groupby(['method', 'metric'])['value'].agg(['mean', 'std', 'count']).reset_index()
        grouped.columns = ['method', 'metric', 'value', 'std_dev', 'n_runs']
        grouped['std_dev'] = grouped['std_dev'].fillna(0.0)
        grouped.to_csv('results.csv', index=False)
    else:
        pd.DataFrame(columns=['method', 'metric', 'value', 'std_dev', 'n_runs']).to_csv('results.csv', index=False)
