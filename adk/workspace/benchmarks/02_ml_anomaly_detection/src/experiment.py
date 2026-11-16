"""Experiment entrypoint for comparing baseline vs ensemble."""
from typing import List
import src.data_types as dt
from src.config import get_channels, get_noise_levels, get_anomaly_rate, get_n_repetitions, get_seeds, get_results_dir
import numpy as np
import pandas as pd
from src.config import CHANNELS, NOISE_LEVELS, ANOMALY_RATE, N_REPETITIONS, SEEDS, RESULTS_DIR
from src.data_generator import generate_dataset
from src.methods.baseline_zscore import ZScoreBaseline
from src.methods.robust_ensemble import RobustEnsemble

def run_experiment() -> pd.DataFrame:
    """Run the full comparison experiment across seeds and noise levels.

    Returns:
        pd.DataFrame: A DataFrame with columns ['method', 'seed', 'noise_level', 'precision', 'recall', 'f1_score', 'auc_roc']
        containing metrics for each method and configuration combination.
    """
    import os
    from src.data_types import compute_metrics, SignalSample, DetectionResult
    seeds = get_seeds()
    noise_levels = get_noise_levels()
    channels = get_channels()
    ensemble_size = get_ensemble_size()
    data_dir = get_data_dir()
    results_base_dir = os.path.join(data_dir, get_results_dir())
    results_list: list[dict] = []
    for seed in seeds:
        np.random.seed(seed)
        for noise_level in noise_levels:
            samples = generate_dataset(channels=channels, noise_levels=[noise_level], n_samples=100, seeds=[seed])
            z_baseline = ZScoreBaseline(threshold=3.0)
            z_baseline.fit(samples)
            z_predictions: list[DetectionResult] = [z_baseline.predict(s) for s in samples]
            base_metrics = compute_metrics(z_predictions, samples)
            results_list.append({'method': 'ZScoreBaseline', 'seed': seed, 'noise_level': noise_level, 'precision': round(base_metrics['precision'], 4), 'recall': round(base_metrics['recall'], 4), 'f1_score': round(base_metrics['f1_score'], 4), 'auc_roc': round(base_metrics['auc_roc'], 4)})
            ensemble = RobustEnsemble(ensemble_size=ensemble_size, threshold=0.5)
            ensemble.fit(samples)
            ens_predictions: list[DetectionResult] = [ensemble.predict(s) for s in samples]
            ens_metrics = compute_metrics(ens_predictions, samples)
            results_list.append({'method': 'RobustEnsemble', 'seed': seed, 'noise_level': noise_level, 'precision': round(ens_metrics['precision'], 4), 'recall': round(ens_metrics['recall'], 4), 'f1_score': round(ens_metrics['f1_score'], 4), 'auc_roc': round(ens_metrics['auc_roc'], 4)})
    os.makedirs(results_base_dir, exist_ok=True)
    csv_path = os.path.join(results_base_dir, 'experiment_results.csv')
    results_df = pd.DataFrame(results_list)
    results_df.to_csv(csv_path, index=False)
    return results_df

def __init__(self, threshold: float=3.0) -> None:
    """Initialize the ZScoreBaseline with a detection threshold.

    Args:
        threshold: The z-score threshold above which a sample is flagged as anomalous.
    """
    pass

def fit(self, samples: List[dt.SignalSample]) -> None:
    """Compute the global mean and standard deviation of features from all samples.

    Args:
        samples: A list of SignalSample objects to compute statistics from.
    """
    if not samples:
        return
    all_values = []
    for s in samples:
        feature_means = [np.mean(s.timestamps[c_idx]) for c_idx in range(len(s.channels))]
        all_values.extend(feature_means)
    self.mean = np.mean(all_values)
    self.std = np.std(all_values)

def predict(self, sample: dt.SignalSample) -> dt.DetectionResult:
    """Predict whether a single sample is anomalous based on z-score.

    Args:
        sample: A SignalSample to classify.

    Returns:
        DetectionResult: Object containing the anomaly flag and score.
    """
    if self.mean is None or self.std is None:
        return dt.DetectionResult(is_anomaly=False, score=0.0)
    z_scores = []
    for c_idx in range(len(sample.channels)):
        channel_mean = np.mean(sample.timestamps[c_idx])
        z = abs((channel_mean - self.mean) / self.std)
        z_scores.append(z)
    score = max(z_scores)
    is_anomaly = score > 3.0
    return dt.DetectionResult(is_anomaly=is_anomaly, score=score)

def run_experiment() -> pd.DataFrame:
    """Run the full comparison experiment across seeds and noise levels.
    Returns a DataFrame with metrics for each method."""
    all_results = []
    for seed in get_seeds():
        for noise_level in get_noise_levels():
            samples = generate_dataset(channels=get_channels(), noise_levels=[noise_level], n_samples=100, seeds=[seed])
            z_baseline = ZScoreBaseline(threshold=3.0)
            z_baseline.fit(samples)
            z_predictions = [z_baseline.predict(s) for s in samples]
            from src.data_types import compute_metrics
            base_metrics = compute_metrics(z_predictions, samples)
            all_results.append({'method': 'ZScoreBaseline', 'seed': seed, 'noise_level': noise_level, 'precision': round(base_metrics['precision'], 4), 'recall': round(base_metrics['recall'], 4), 'f1_score': round(base_metrics['f1_score'], 4), 'auc_roc': round(base_metrics['auc_roc'], 4)})
            ensemble = RobustEnsemble(ensemble_size=get_ensemble_size(), threshold=0.5)
            ensemble.fit(samples)
            ens_predictions = [ensemble.predict(s) for s in samples]
            ens_metrics = compute_metrics(ens_predictions, samples)
            all_results.append({'method': 'RobustEnsemble', 'seed': seed, 'noise_level': noise_level, 'precision': round(ens_metrics['precision'], 4), 'recall': round(ens_metrics['recall'], 4), 'f1_score': round(ens_metrics['f1_score'], 4), 'auc_roc': round(ens_metrics['auc_roc'], 4)})
    results_df = pd.DataFrame(all_results)
    return results_df

def run_experiment() -> pd.DataFrame:
    """Run the full comparison experiment across seeds and noise levels.

    Returns:
        pd.DataFrame: A DataFrame with columns ['method', 'seed', 'noise_level', 'precision', 'recall', 'f1_score', 'auc_roc']
        containing metrics for each method and configuration combination.
    """
    from src.data_types import compute_metrics
    results_list = []
    seeds = get_seeds()
    noise_levels = get_noise_levels()
    channels = get_channels()
    anomaly_rate = get_anomaly_rate()
    ensemble_size = get_ensemble_size()
    data_dir = get_data_dir()
    results_base_dir = os.path.join(data_dir, get_results_dir())
    np.random.seed(0)
    for seed in seeds:
        np.random.seed(seed)
        for noise_level in noise_levels:
            samples = generate_dataset(channels=channels, noise_levels=[noise_level], n_samples=100, seeds=[seed])
            z_baseline = ZScoreBaseline(threshold=3.0)
            z_baseline.fit(samples)
            z_predictions = [z_baseline.predict(s) for s in samples]
            base_metrics = compute_metrics(z_predictions, samples)
            results_list.append({'method': 'ZScoreBaseline', 'seed': seed, 'noise_level': noise_level, 'precision': round(base_metrics['precision'], 4), 'recall': round(base_metrics['recall'], 4), 'f1_score': round(base_metrics['f1_score'], 4), 'auc_roc': round(base_metrics['auc_roc'], 4)})
            ensemble = RobustEnsemble(ensemble_size=ensemble_size, threshold=0.5)
            ensemble.fit(samples)
            ens_predictions = [ensemble.predict(s) for s in samples]
            ens_metrics = compute_metrics(ens_predictions, samples)
            results_list.append({'method': 'RobustEnsemble', 'seed': seed, 'noise_level': noise_level, 'precision': round(ens_metrics['precision'], 4), 'recall': round(ens_metrics['recall'], 4), 'f1_score': round(ens_metrics['f1_score'], 4), 'auc_roc': round(ens_metrics['auc_roc'], 4)})
    csv_path = os.path.join(results_base_dir, 'experiment_results.csv')
    results_df = pd.DataFrame(results_list)
    results_df.to_csv(csv_path, index=False)
    return results_df

def predict(self, sample: dt.SignalSample) -> dt.DetectionResult:
    """Predict whether a single sample is anomalous based on z-score.

    Args:
        sample: A SignalSample to classify.

    Returns:
        DetectionResult: Object containing the anomaly flag and score.
    """
    if self.mean is None or self.std is None:
        return dt.DetectionResult(is_anomaly=False, score=0.0)
    z_scores = []
    for c_idx in range(len(sample.channels)):
        channel_mean = np.mean(sample.timestamps[c_idx])
        z = abs((channel_mean - self.mean) / self.std)
        z_scores.append(z)
    score = max(z_scores)
    is_anomaly = score > 3.0
    return dt.DetectionResult(is_anomaly=is_anomaly, score=score)
