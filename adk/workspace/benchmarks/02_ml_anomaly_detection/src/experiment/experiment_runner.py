"""Experiment runner for anomaly detection comparison.

Initializes the data generator and evaluation pipeline to compare
UnivariateZScoreDetector against EnsembleDetector across multiple repetitions.
Results are aggregated and saved to results/final_results.json.
"""
import pandas as pd
import json
import os
from typing import Any, Dict
import numpy as np
import sys
if 'src' not in sys.path:
    sys.path.insert(0, './src')
from config import Hyperparameters
from src.data.synthetic_data_generator import BioSignalGenerator
from src.detectors.baseline_zscore import UnivariateZScoreDetector
from src.detectors.ensemble_detector import EnsembleDetector
from src.evaluation.metrics import evaluate_detector

def run_all() -> pd.DataFrame:
    """Execute the experiment comparing ensemble vs baseline detectors and save results.

    Reads settings from config.Hyperparameters, runs detection experiments for each method,
    and saves aggregated metrics to results/final_results.json. Returns a pandas DataFrame of results.
    """
    params: Hyperparameters = Hyperparameters()
    n_runs: int = params.num_repetitions
    seed_base: int = params.seed
    generator = BioSignalGenerator(signal_config=params.signal_config, anomaly_config=params.anomaly_config)
    results_list: list[Dict[str, Any]] = []
    baseline_detector = UnivariateZScoreDetector(threshold=params.threshold_zscore)
    ensemble_config = params.ensemble_config
    ensemble_detector = EnsembleDetector(config=ensemble_config, sensitivity_params=ensemble_config.sensitivity_params)
    detectors: Dict[str, Any] = {'UnivariateZScore': baseline_detector, 'EnsembleDetector': ensemble_detector}
    for method_name, detector in detectors.items():
        method_f1_scores: list[float] = []
        method_roc_aucs: list[float] = []
        method_delays: list[float] = []
        for i in range(n_runs):
            current_seed = seed_base + i
            rng = np.random.default_rng(current_seed)
            X, labels, anomaly_events = generator.generate_dataset(length=params.sample_length, n_segments=params.n_segments, rng=rng)
            metrics_dict: Dict[str, float] = evaluate_detector(detector=detector, X=X, y_true=labels, anomaly_events=anomaly_events, rng=rng)
            method_f1_scores.append(metrics_dict['f1_score'])
            method_roc_aucs.append(metrics_dict['roc_auc'])
            method_delays.append(metrics_dict['detection_delay'])
        results_list.append({'method': method_name, 'mean_f1_score': float(np.mean(method_f1_scores)), 'std_f1_score': float(np.std(method_f1_scores)), 'mean_roc_auc': float(np.mean(method_roc_aucs)), 'detection_delay_mean': float(np.mean(method_delays))})
    os.makedirs('results', exist_ok=True)
    output_path = os.path.join('results', 'final_results.json')
    with open(output_path, 'w') as f:
        json.dump(results_list, f, indent=2)
    print(f'Results saved to {output_path}')
    df_data = []
    for row in results_list:
        for metric_name, value in row.items():
            if metric_name != 'method':
                df_data.append({'method': row['method'], 'metric': metric_name, 'value': value})
    return pd.DataFrame(df_data)

def run_all() -> pd.DataFrame:
    """Execute the experiment comparing ensemble vs baseline detectors and save results.

    Reads settings from config.Hyperparameters, runs detection experiments for each method,
    and saves aggregated metrics to results/final_results.json. Returns a pandas DataFrame of results.
    """
    params: Hyperparameters = Hyperparameters()
    n_runs: int = params.num_repetitions
    seed_base: int = params.seed
    generator = BioSignalGenerator(signal_config=params.signal_config, anomaly_config=params.anomaly_config)
    results_list: list[Dict[str, Any]] = []
    baseline_detector = UnivariateZScoreDetector(threshold=params.threshold_zscore)
    ensemble_config = params.ensemble_config
    ensemble_detector = EnsembleDetector(config=ensemble_config, sensitivity_params=ensemble_config.sensitivity_params)
    detectors: Dict[str, Any] = {'UnivariateZScore': baseline_detector, 'EnsembleDetector': ensemble_detector}
    for method_name, detector in detectors.items():
        method_f1_scores: list[float] = []
        method_roc_aucs: list[float] = []
        method_delays: list[float] = []
        for i in range(n_runs):
            current_seed = seed_base + i
            rng = np.random.default_rng(current_seed)
            X, labels, anomaly_events = generator.generate_dataset(length=params.sample_length, n_segments=params.n_segments, rng=rng)
            metrics_dict: Dict[str, float] = evaluate_detector(detector=detector, X=X, y_true=labels, anomaly_events=anomaly_events, rng=rng)
            method_f1_scores.append(metrics_dict['f1_score'])
            method_roc_aucs.append(metrics_dict['roc_auc'])
            method_delays.append(metrics_dict['detection_delay'])
        results_list.append({'method': method_name, 'mean_f1_score': float(np.mean(method_f1_scores)), 'std_f1_score': float(np.std(method_f1_scores)), 'mean_roc_auc': float(np.mean(method_roc_aucs)), 'detection_delay_mean': float(np.mean(method_delays))})
    os.makedirs('results', exist_ok=True)
    output_path = os.path.join('results', 'final_results.json')
    with open(output_path, 'w') as f:
        json.dump(results_list, f, indent=2)
    print(f'Results saved to {output_path}')
    df_data = []
    for row in results_list:
        for metric_name, value in row.items():
            if metric_name != 'method':
                df_data.append({'method': row['method'], 'metric': metric_name, 'value': value})
    return pd.DataFrame(df_data)
