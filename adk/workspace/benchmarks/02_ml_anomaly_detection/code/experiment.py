"""Orchestrates the repeated experiments for both methods and writes results.csv."""
import os
from data_generation import generate_dataset, SAMPLE_LENGTH, NORMAL_CHANNELS
from base_detector import ZScoreDetector
from subspace_detector import RandomSubspaceDetector
from evaluation import compute_metrics, aggregate_metrics
from score_exporter import export_scores
import numpy as np
import pandas as pd
NUM_RUNS: int = 10
ANOMALIES_PER_SAMPLE: int = 5
BASELINE_THRESHOLD: float = 3.0
OUTPUT_PATH: str = 'results.csv'

def run_experiment() -> None:
    """Orchestrate the full experiment pipeline and write results to CSV.

    This function performs the following steps for each of `NUM_RUNS` independent iterations:
    1. Generates synthetic telemetry data with injected anomalies using `generate_dataset`.
    2. Identifies clean (non-anomalous) samples from the generated data.
    3. Fits the `ZScoreDetector` on clean data and predicts on the full dataset to obtain
       baseline metrics via `compute_metrics`.
    4. Fits the `RandomSubspaceDetector` on clean data, computes anomaly scores,
       determines predictions using a fixed threshold (derived from distribution or default),
       and calculates metrics via `compute_metrics`.
    5. Aggregates metrics across runs using `aggregate_metrics`.
    6. Exports raw scores via `export_scores` for visualization support.
    7. Writes aggregated results to `results.csv` with columns: method, metric, value,
       std_dev (if applicable), n_runs.

    Side Effects:
    - Creates `figures/` directory and writes `scores_for_plots.csv` inside it.
    - Writes `results.csv` in the current working directory.

    Edge Cases:
    - If no clean data is found for fitting, raises ValueError.
    - Ensures deterministic results by seeding each run independently.
    """
    os.makedirs('figures', exist_ok=True)
    per_run_results: list[dict[str, float]] = []
    all_scores: dict[str, np.ndarray] | None = None
    for run_idx in range(NUM_RUNS):
        rng_seed = 42 + run_idx
        np.random.seed(rng_seed)
        result = generate_dataset(n_samples=SAMPLE_LENGTH, n_anomalies=ANOMALIES_PER_SAMPLE, seed=rng_seed)
        if result is None:
            raise ValueError(f'generate_dataset returned None for run {run_idx + 1}')
        telemetry: np.ndarray = result[0]
        labels: np.ndarray = result[1]
        y_true = labels.astype(int)
        clean_mask = y_true == 0
        if not np.any(clean_mask):
            raise ValueError(f'No clean samples found in run {run_idx + 1}. All samples are anomalous or mask logic failed.')
        X_clean = telemetry[clean_mask]
        z_detector = ZScoreDetector(threshold=BASELINE_THRESHOLD)
        z_detector.fit(X_clean)
        baseline_scores = z_detector.get_anomaly_scores()
        y_pred_baseline, _ = z_detector.predict(BASELINE_THRESHOLD)
        baseline_metrics = compute_metrics(y_true=y_true, y_pred=y_pred_baseline, scores=baseline_scores)
        rs_detector = RandomSubspaceDetector(n_estimators=N_ESTIMATORS, subspace_dim=SUBSPACE_DIMENSION, seed=rng_seed)
        rs_detector.fit(X_clean)
        subspace_scores = rs_detector.get_anomaly_scores()
        ref_mean = np.mean(subspace_scores[clean_mask])
        ref_std = np.std(subspace_scores[clean_mask])
        subspace_threshold = max(ref_mean + 3 * ref_std, ref_mean + 2 * ref_std)
        y_pred_subspace, _ = rs_detector.predict(subspace_threshold)
        subspace_metrics = compute_metrics(y_true=y_true, y_pred=y_pred_subspace, scores=subspace_scores)
        all_metrics_zscore = {'method': 'ZScore', **baseline_metrics}
        all_metrics_subspace = {'method': 'RandomSubspace', **subspace_metrics}
        per_run_results.append(all_metrics_zscore)
        per_run_results.append(all_metrics_subspace)
        if all_scores is None:
            all_scores = {'y_true': y_true, 'baseline_scores': baseline_scores, 'subspace_scores': subspace_scores}
        else:
            all_scores['y_true'] = np.concatenate([all_scores['y_true'], y_true])
            all_scores['baseline_scores'] = np.concatenate([all_scores['baseline_scores'], baseline_scores])
            all_scores['subspace_scores'] = np.concatenate([all_scores['subspace_scores'], subspace_scores])
    zscore_runs = [item for item in per_run_results if item['method'] == 'ZScore']
    subspace_runs = [item for item in per_run_results if item['method'] == 'RandomSubspace']

    def safe_mean_std_list(lst: list[float]) -> tuple:
        """Compute mean and std deviation for a list of numeric values."""
        if not lst:
            return (None, None)
        means = [float(item) if hasattr(item, '__iter__') else float(item) for item in lst]
        stds = [np.std(item) if hasattr(item, '__iter__') and len(item) > 1 else 0.0 for item in lst]
        return (np.mean(means), np.std(means) if len(means) > 1 else 0.0)
    zscore_aggregated = {}
    for metric_name in ['AUC_ROC', 'F1_SCORE', 'PRECISION', 'RECALL', 'SPECIFICITY']:
        val, std_dev = safe_mean_std_list([r[metric_name] for r in zscore_runs])
        n = len(zscore_runs)
        zscore_aggregated[metric_name] = {'value': val, 'std_dev': std_dev, 'n_runs': n}
    subspace_aggregated = {}
    for metric_name in ['AUC_ROC', 'F1_SCORE', 'PRECISION', 'RECALL', 'SPECIFICITY']:
        val, std_dev = safe_mean_std_list([r[metric_name] for r in subspace_runs])
        n = len(subspace_runs)
        subspace_aggregated[metric_name] = {'value': val, 'std_dev': std_dev, 'n_runs': n}
    csv_rows: list[dict[str, float | str]] = []
    methods: list[str] = ['ZScore', 'RandomSubspace']
    metrics_order: list[str] = ['AUC_ROC', 'F1_SCORE', 'PRECISION', 'RECALL', 'SPECIFICITY']
    for method in methods:
        data_map = zscore_aggregated if method == 'ZScore' else subspace_aggregated
        for metric in metrics_order:
            val = data_map[metric]['value']
            std_val = data_map[metric]['std_dev']
            n_runs = data_map[metric]['n_runs']
            csv_rows.append({'method': method, 'metric': metric, 'value': val, 'std_dev': std_val, 'n_runs': n_runs})
    if all_scores is not None:
        export_scores(dataset_y_true=all_scores['y_true'], baseline_scores=all_scores['baseline_scores'], subspace_scores=all_scores['subspace_scores'])
    df = pd.DataFrame(csv_rows)
    df.to_csv(OUTPUT_PATH, index=False)

def mean(x):
    return np.mean(x)

def std(x):
    return np.std(x) if len(x) > 0 else 0.0
