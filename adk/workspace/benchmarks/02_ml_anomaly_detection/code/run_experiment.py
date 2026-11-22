"""Orchestrates the anomaly detection experiment: generates data, trains detectors, computes metrics, and writes results.csv."""
import os
from typing import List
import numpy as np
import pandas as pd
from synth_data import generate_dataset
from baseline_zscore import ZScoreBaseline
from method_rse import RandomSubspaceDetector
from metrics import calculate_auc_roc, calculate_f1_score
N_RUNS: int = 20
N_SAMPLES: int = 5000
N_CHANNELS: int = 5
ANOMALY_FRACTION: float = 0.05
BASE_SEED: int = 42
RSE_THRESHOLD_SIGMAS: float = 2.0
N_ESTIMATORS: int = 50
SUBSAMPLE_RATIO: float = 0.8

def run_study() -> None:
    """Run the full anomaly detection study and write results to `results.csv`.

    Executes ``N_RUNS`` independent experiments. In each run:
    1. Synthetic data is generated with injected anomalies using a deterministic seed derived from the run index.
    2. A baseline Z-score detector (``ZScoreBaseline``) is fitted and used for prediction.
       The baseline produces binary labels directly.
    3. The proposed Random Subspace Ensemble detector (``RandomSubspaceDetector``) is fitted and used for prediction.
       It produces continuous anomaly scores. These scores are converted to binary labels using a sigma-threshold
       heuristic (mean + RSE_THRESHOLD_SIGMAS * std) for F1-score calculation, and passed raw for AUC-ROC calculation.
    4. Metrics AUC-ROC and F1-score are calculated for both methods against the ground truth mask.
       - For AUC-ROC, continuous scores are used because the metric computes ROC over thresholds internally.
       - For F1-score, binary predictions (thresholded from raw scores) are used.

    Results are aggregated across runs, computing mean and standard deviation for each metric per method,
    and written to ``results.csv`` in the current working directory with columns: ``method``, ``metric``, 
    ``value``, ``std_dev``, ``n_runs``.

    The file is written in the workspace root (current directory). Existing files are overwritten.
    """
    raise NotImplementedError
