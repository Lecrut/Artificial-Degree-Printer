"""Runs the full experimental loop: generates data, trains detectors, evaluates metrics, and writes results.csv."""
from typing import Dict, List
import numpy as np
import pandas as pd
from evaluation import compute_metrics, aggregate_results, N_RUNS
from baselines import ZScoreDetector
from rs_ensemble import RSADetector
from data_generation import generate_dataset

def run_experiment() -> None:
    """Run the full experiment: generate data, train detectors, evaluate metrics, and write results.csv.

    Iterates over `N_RUNS` repetitions to ensure statistical validity. For each repetition:
    1. Generates synthetic multi-channel physiological data with injected anomalies.
    2. Splits data into training (clean) and test sets.
    3. Fits the Random Subspace Ensemble detector on training data, then scores test data.
    4. Fits the static Z-Score baseline on training data, then scores test data.
    5. Computes metrics using appropriate thresholds for each detector's output scale.
    6. Aggregates results across all runs and writes to CSV.

    Returns None.
    """
    raise NotImplementedError
