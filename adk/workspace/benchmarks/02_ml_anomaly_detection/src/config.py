"""Configuration module for the anomaly detection experiment.

This module defines global constants and configuration functions used across the
experiment, data generation, and evaluation pipelines. All values are read here,
either as direct literals or via these helper functions, ensuring reproducibility
and clear citation in academic reports.

Public API:
    - get_channels: Return list of bio-signal channels.
    - get_noise_levels: Return list of noise amplitude factors.
    - get_anomaly_rate: Return target anomaly probability (5%).
    - get_ensemble_size: Return number of estimators in robust ensemble.
    - get_n_repetitions: Return number of experimental trials.
    - get_seeds: Return list of random seeds for reproducibility.
    - get_test_split: Return fraction of data reserved for validation.
    - get_data_dir: Return root path for raw input data.
    - get_results_dir: Return root path for output metrics and plots.
    - CHANNELS, NOISE_LEVELS, ANOMALY_RATE, DATA_DIR: Direct constant exports.
"""
import os
from typing import List
CHANNELS: List[str] = ['EEG', 'ECG', 'EMG']
NOISE_LEVELS: List[float] = [0.1, 0.5, 1.0]
ANOMALY_RATE: float = 0.05
DATA_DIR: str = 'data'
_CHANNELS_LIST: List[str] = CHANNELS
_NOISE_LEVELS: List[float] = NOISE_LEVELS
_N_REPETITIONS: int = 5
_SEEDS_LIST: List[int] = list(range(5))
_TEST_SPLIT_FRACTION: float = 0.2
_RESULTS_ROOT_PATH: str = 'results'
_ENSEMBLE_SIZE: int = 10
_ANOMALY_RATE_INTERNAL: float = ANOMALY_RATE

def get_channels() -> List[str]:
    """Return the list of bio-signal telemetry channels.

    Returns:
        List[str]: The channel identifiers ('EEG', 'ECG', 'EMG').
    """
    return _CHANNELS_LIST

def get_noise_levels() -> List[float]:
    """Return the noise levels for synthetic signal generation.

    Returns:
        List[float]: Noise factors [0.1, 0.5, 1.0].
    """
    return _NOISE_LEVELS

def get_anomaly_rate() -> float:
    """Return the target anomaly rate for detection.

    Returns:
        float: Probability of an anomaly (5%).
    """
    return _ANOMALY_RATE_INTERNAL

def get_ensemble_size() -> int:
    """Return the size of the robust ensemble detector.

    Returns:
        int: Number of base estimators (10).
    """
    return _ENSEMBLE_SIZE

def get_n_repetitions() -> int:
    """Return the number of experimental repetitions.

    Returns:
        int: Trial count (5).
    """
    return _N_REPETITIONS

def get_seeds() -> List[int]:
    """Return the list of random seeds for reproducibility.

    Returns:
        List[int]: Sequential seeds [0, 1, 2, 3, 4].
    """
    return _SEEDS_LIST

def get_test_split() -> float:
    """Return the fraction of data used for testing.

    Returns:
        float: Validation split ratio (0.2).
    """
    return _TEST_SPLIT_FRACTION

def get_data_dir() -> str:
    """Return the root directory path for raw data.

    Returns:
        str: Absolute or relative path to 'data' folder.
    """
    return DATA_DIR

def get_results_dir() -> str:
    """Return the root directory path for experimental results.

    Returns:
        str: Absolute or relative path to 'results' folder.
    """
    return _RESULTS_ROOT_PATH

def get_results_dir() -> str:
    """Return the root directory path for experimental results.

    Returns:
        str: Absolute or relative path to 'results' folder.
    """
    return RESULTS_DIR
