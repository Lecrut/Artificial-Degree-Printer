"""Configuration module for Bio-Signal & Telemetry Anomaly Detection.

Defines hyperparameters for synthetic data generation and detector thresholds.

Attributes:
    N_SAMPLES (int): Number of samples in the synthetic bio-signal dataset.
    ANOMALY_RATIO (float): Proportion of anomalous samples in the dataset.
    Z_THRESHOLD (float): Standard deviation threshold for Z-score baseline.
    ENSEMBLE_TREES (int): Number of trees in the Adaptive Robust Mahalanobis ensemble.
"""

# Synthetic dataset parameters
N_SAMPLES: int = 600
ANOMALY_RATIO: float = 0.08

# Detector parameters
Z_THRESHOLD: float = 2.4
ENSEMBLE_TREES: int = 25
