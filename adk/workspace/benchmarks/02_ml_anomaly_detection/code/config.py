"""
Configuration constants for Bio-Signal & Telemetry Anomaly Detection.

This module defines hyperparameters and global constants required by the
core detection algorithms, testing suite, and visualization scripts.
"""
from typing import Final

# Hyperparameter: Number of synthetic samples per class/segment
N_SAMPLES: Final[int] = 600

# Hyperparameter: Ratio of anomalous data points within the dataset
ANOMALY_RATIO: Final[float] = 0.08

# Hyperparameter: Z-score threshold for static baseline detection
Z_THRESHOLD: Final[float] = 2.4

# Hyperparameter: Number of trees in the Robust Mahalanobis Ensemble
ENSEMBLE_TREES: Final[int] = 25
