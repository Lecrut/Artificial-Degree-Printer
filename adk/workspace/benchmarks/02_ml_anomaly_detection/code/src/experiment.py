"""Experiment entrypoint for comparing Ensemble vs Baseline."""
import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve, auc, precision_recall_fscore_support
import src.data_generator as data_gen
import src.ensemble_detector as ens_det
import src.baseline_zscore as base_det
N_CHANNELS: int = 3
SIGNAL_LENGTH: int = 1000
N_ANOMALIES: int = 5
REPEATS: int = 10
SEEDS: list[int] = [42, 123, 456]

def run_experiment() -> None:
    """Run the full experiment pipeline.

    Generates data using src.data_generator with n_channels=N_CHANNELS,
    signal_length=SIGNAL_LENGTH, and N_ANOMALIES anomalies for each seed in SEEDS,
    repeating REPEATS times per seed. Runs src.ensemble_detector.RandomSubspaceEnsemble
    and src.baseline_zscore.ZScoreBaseline on the generated data.
    Crucially transposes X (X.T) before passing to ensemble.fit() to satisfy 
    (n_samples, n_features) contract. Explicitly fits on X.T and predicts on X.T.
    Computes metrics: Precision/Recall/F1 using sklearn.metrics.precision_recall_fscore_support(y_true, preds),
    and AUC-ROC using sklearn.metrics.roc_curve(y_true, scores). Saves results to `results.csv`.
    Calls src.plotting.plots() at the end.
    """
    np.random.seed(42)
    methods = ['zscore', 'ensemble']
    all_results = []
    for seed in SEEDS:
        results_per_seed: list[dict[str, float]] = []
        for _ in range(REPEATS):
            X_gen, anomalies = data_gen.generate_signal(N_CHANNELS, SIGNAL_LENGTH, N_ANOMALIES, seed=seed)
            y_true_full = np.zeros((SIGNAL_LENGTH, N_CHANNELS), dtype=bool)
            for anom in anomalies:
                start, end = (anom['start'], anom['end'])
                y_true_full[start:end + 1] = True
            pass
            z_scores_zscore = []
            anomalies_per_channel: list[int] = []
            for c in range(N_CHANNELS):
                x_c = X_gen[c].reshape(-1, 1)
                detector = base_det.ZScoreBaseline(window_size=SIGNAL_LENGTH // 2, threshold=3.0)
                scores = detector.compute_scores(x_c)
                z_scores_zscore.append(scores.flatten())
            z_scores_combined = np.hstack(z_scores_zscore)
            X_zscore_input = X_gen.T[:, :1]
            ensemble_detector_obj = ens_det.RandomSubspaceEnsemble(n_estimators=10, subspace_size=3, contamination=0.1, seed=seed)
            ensemble_detector_obj.fit(X_gen.T)
            scores_ensemble = ensemble_detector_obj.predict_scores(X_gen.T)
            detector_zscore = base_det.ZScoreBaseline(window_size=SIGNAL_LENGTH // 2, threshold=3.0)
            x_single = X_gen[:, 0].reshape(-1, 1)
            scores_zscore = detector_zscore.compute_scores(x_single)
            y_true_full = np.zeros((SIGNAL_LENGTH, N_CHANNELS), dtype=bool)
            for anom in anomalies:
                start, end = (anom['start'], anom['end'])
                y_true_full[start:end + 1] = True
            scores_ensemble_flat = np.max(scores_ensemble, axis=1).flatten()
            scores_zscore_flat = scores_zscore.flatten()
            y_true_flat = y_true_full.reshape(-1)
            y_true_flat = np.any(y_true_full, axis=1)
            thresh_ensemble = np.percentile(scores_ensemble_flat, 98.5)
            thresh_zscore = np.percentile(scores_zscore_flat, 98.5)
            preds_ensemble = (scores_ensemble_flat > thresh_ensemble).astype(int)
            preds_zscore = (scores_zscore_flat > thresh_zscore).astype(int)
            precision_zr, recall_zr, _ = precision_recall_fscore_support(y_true_flat, preds_zscore)
            f1_zr = 2 * precision_zr * recall_zr / (precision_zr + recall_zr) if precision_zr + recall_zr > 0 else 0
            precision_en, recall_en, _ = precision_recall_fscore_support(y_true_flat, preds_ensemble)
            f1_en = 2 * precision_en * recall_en / (precision_en + recall_en) if precision_en + recall_en > 0 else 0
            auc_zr = auc(scores_zscore_flat, y_true_flat.astype(int))
            auc_en = auc(scores_ensemble_flat, y_true_flat.astype(int))
            results_per_seed.append({'method': 'zscore', 'metric': 'F1', 'value': float(f1_zr), 'std_dev': 0.0, 'n_runs': REPEATS})
            pass
    all_metrics = []
    for seed in SEEDS:
        metrics_data: list[dict] = []
        for run_idx in range(REPEATS):
            X_gen, anomalies = data_gen.generate_signal(N_CHANNELS, SIGNAL_LENGTH, N_ANOMALIES, seed=seed)
            y_true_full = np.zeros((SIGNAL_LENGTH, N_CHANNELS), dtype=bool)
            for anom in anomalies:
                start, end = (anom['start'], anom['end'])
                y_true_full[start:end + 1] = True
            x_z = X_gen[:, 0].reshape(-1, 1)
            det_z = base_det.ZScoreBaseline(window_size=SIGNAL_LENGTH // 2, threshold=3.0)
            sc_z = det_z.compute_scores(x_z).flatten()
            preds_z = (sc_z > np.percentile(sc_z, 98.5)).astype(int)
            det_ens = ens_det.RandomSubspaceEnsemble(n_estimators=10, subspace_size=N_CHANNELS, contamination=0.1, seed=seed)
            sc_ens = det_ens.predict_scores(X_gen.T).flatten()
            preds_ens = (sc_ens > np.percentile(sc_ens, 98.5)).astype(int)
            y_true_flat = np.any(y_true_full, axis=1)
            p_z, r_z, _ = precision_recall_fscore_support(y_true_flat, preds_z)
            f1_z = 2 * p_z * r_z / (p_z + r_z) if p_z + r_z > 0 else 0
            auc_z = auc(sc_z, y_true_flat.astype(int))
            p_e, r_e, _ = precision_recall_fscore_support(y_true_flat, preds_ens)
            f1_e = 2 * p_e * r_e / (p_e + r_e) if p_e + r_e > 0 else 0
            auc_e = auc(sc_ens, y_true_flat.astype(int))
            metrics_data.append({'method': 'zscore', 'metric': 'F1', 'value': float(f1_z), 'std_dev': 0.0, 'n_runs': REPEATS})
            metrics_data.append({'method': 'ensemble', 'metric': 'F1', 'value': float(f1_e), 'std_dev': 0.0, 'n_runs': REPEATS})
    methods = []
    metrics_list = {}
    f1_counts: dict = {'zscore': [], 'ensemble': []}
    auc_counts: dict = {'zscore': [], 'ensemble': []}
    for seed in SEEDS:
        X_gen, anomalies = data_gen.generate_signal(N_CHANNELS, SIGNAL_LENGTH, N_ANOMALIES, seed=seed)
        y_true_full = np.zeros((SIGNAL_LENGTH, N_CHANNELS), dtype=bool)
        for anom in anomalies:
            start, end = (anom['start'], anom['end'])
            y_true_full[start:end + 1] = True
        x_z = X_gen[:, 0].reshape(-1, 1)
        det_z = base_det.ZScoreBaseline(window_size=SIGNAL_LENGTH // 2, threshold=3.0)
        sc_z = det_z.compute_scores(x_z).flatten()
        preds_z = (sc_z > np.percentile(sc_z, 98.5)).astype(int)
        y_true_flat = np.any(y_true_full, axis=1)
        p_z, r_z, _ = precision_recall_fscore_support(y_true_flat, preds_z)
        f1_z = 2 * p_z * r_z / (p_z + r_z) if p_z + r_z > 0 else 0
        auc_z = auc(sc_z, y_true_flat.astype(int))
        det_ens = ens_det.RandomSubspaceEnsemble(n_estimators=10, subspace_size=N_CHANNELS, contamination=0.1, seed=seed)
        sc_ens = det_ens.predict_scores(X_gen.T).flatten()
        preds_ens = (sc_ens > np.percentile(sc_ens, 98.5)).astype(int)
        p_e, r_e, _ = precision_recall_fscore_support(y_true_flat, preds_ens)
        f1_e = 2 * p_e * r_e / (p_e + r_e) if p_e + r_e > 0 else 0
        auc_e = auc(sc_ens, y_true_flat.astype(int))
        methods.append('zscore')
        f1_counts['zscore'].append(f1_z)
        auc_counts['zscore'].append(auc_z)
        methods.append('ensemble')
        f1_counts['ensemble'].append(f1_e)
        auc_counts['ensemble'].append(auc_e)

    def calc_stats(vals):
        mean_v = np.mean(vals)
        std_v = np.std(vals) if len(vals) > 1 else 0.0
        n = len(vals)
        return (mean_v, std_v, n)
    z_f1_mean, z_f1_std, z_n = calc_stats(f1_counts['zscore'])
    e_f1_mean, e_f1_std, e_n = calc_stats(f1_counts['ensemble'])
    z_auc_mean, z_auc_std, z_an = calc_stats(auc_counts['zscore'])
    e_auc_mean, e_auc_std, e_an = calc_stats(f1_counts['ensemble'])
    results_df = pd.DataFrame({'method': methods, 'metric': [f1_z for _ in f1_counts.keys()]})
    rows = [{'method': 'zscore', 'metric': 'F1', 'value': z_f1_mean, 'std_dev': z_f1_std, 'n_runs': len(methods)}, {'method': 'ensemble', 'metric': 'F1', 'value': e_f1_mean, 'std_dev': e_f1_std, 'n_runs': len(methods)}, {'method': 'zscore', 'metric': 'AUC-ROC', 'value': z_auc_mean, 'std_dev': z_auc_std, 'n_runs': z_an}, {'method': 'ensemble', 'metric': 'AUC-ROC', 'value': e_auc_mean, 'std_dev': e_auc_std, 'n_runs': e_an}]
    df = pd.DataFrame(rows)
    df = df.sort_values(['method', 'metric'])
    df.to_csv('results.csv', index=False)
    src.plotting.plots()
