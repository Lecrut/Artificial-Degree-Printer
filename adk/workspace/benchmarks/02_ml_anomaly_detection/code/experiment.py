"""Główny moduł eksperymentu: przeprowadza pomiary dla obu metod, agreguje wyniki i zapisuje je do results.csv."""
import numpy as np
import pandas as pd
from data_generation import generate_physio_data
from baseline_detector import BaselineZScore
from rs_ensemble_detector import RandomSubspaceEnsemble
from evaluation_metrics import compute_f1, compute_auc
N_RUNS: int = 10
N_CHANNELS: int = 4
LENGTH: int = 500
ANOMALY_RATE: float = 0.01
Z_THRESHOLD: float = 3.0
ENSEMBLE_ESTIMATORS: int = 50
ENSEMBLE_SUBSPACE_DIM: int = 2
ENSEMBLE_THRESHOLD: float = 2.0

def run_experiment() -> None:
    """Przeprowadza eksperyment porównujący detektor bazowy i proponowany.

    Dla każdej z N_RUNS powtórzeń:
    1. Generuje syntetyczne dane wielokanałowe z wstrzykniętymi anomaliami.
    2. Tworzy jednowymiarową maskę etykiet truth (True jeśli którykolwiek kanał 
       w danym czasie jest anomalią).
    3. Uruchamia BaselineZScore i RandomSubspaceEnsemble.
    4. Pozyskuje surowe, ciągłe wyniki detekcji (scores) od obu detektorów
       oraz binarne predykcje. Oblicza metryki f1_score (z predykcji) 
       oraz auc_score (ze zbioru predykcji i raw scores w stosunku do truth).
    5. Agreguje wyniki ze wszystkich powtórzeń.

    Wyniki końcowe są zapisywane do pliku results.csv w głównym katalogu pracy, 
    zawierającego kolumny: method, metric, value (średnia), std_dev (odchylenie standardowe).
    """
    import os
    import sys
    results_store = []
    for run in range(N_RUNS):
        rng = np.random.default_rng(run + 1)
        data_dict = generate_physio_data(n_channels=N_CHANNELS, length=LENGTH, anomaly_rate=ANOMALY_RATE)
        X = data_dict['data']
        Y_truth_2d = data_dict['labels']
        Y_truth_1d = np.any(Y_truth_2d > 0, axis=1)
        detector_baseline = BaselineZScore(threshold=Z_THRESHOLD)
        preds_baseline_bool = detector_baseline.detect(X[:, 0])
        f1_score_run = compute_f1(Y_truth_1d, preds_baseline_bool)
        mean_val = np.mean(X[:, 0])
        std_val = np.std(X[:, 0])
        if std_val == 0:
            z_scores_run = np.zeros_like(X[:, 0])
        else:
            z_scores_run = (X[:, 0] - mean_val) / std_val
        auc_score_run = compute_auc(Y_truth_1d, z_scores_run)
        detector_ensemble = RandomSubspaceEnsemble(n_estimators=ENSEMBLE_ESTIMATORS, subspace_dim=ENSEMBLE_SUBSPACE_DIM, threshold=ENSEMBLE_THRESHOLD)
        detector_ensemble.fit(X)
        preds_ensemble_bool = detector_ensemble.detect(X)
        scores_ensemble = detector_ensemble.get_anomaly_scores(X)
        f1_score_run_ensemble = compute_f1(Y_truth_1d, preds_ensemble_bool)
        auc_score_run_ensemble = compute_auc(Y_truth_1d, scores_ensemble)
        results_store.append({'method': 'baseline', 'metric': 'f1_score', 'value': float(f1_score_run), 'std_dev': 0.0, 'n_runs': N_RUNS})
        results_store.append({'method': 'baseline', 'metric': 'auc_score', 'value': float(auc_score_run), 'std_dev': 0.0, 'n_runs': N_RUNS})
        results_store.append({'method': 'ensemble', 'metric': 'f1_score', 'value': float(f1_score_run_ensemble), 'std_dev': 0.0, 'n_runs': N_RUNS})
        results_store.append({'method': 'ensemble', 'metric': 'auc_score', 'value': float(auc_score_run_ensemble), 'std_dev': 0.0, 'n_runs': N_RUNS})
    df_results = pd.DataFrame(results_store)
    aggregated_df = df_results.groupby(['method', 'metric']).agg({'value': 'mean', 'std_dev': lambda x: x.iloc[0], 'n_runs': 'first'}).reset_index()
    output_path = os.path.join(os.path.dirname(__file__), 'results.csv')
    aggregated_df.to_csv(output_path, index=False)
