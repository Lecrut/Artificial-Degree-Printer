"""
Hyperparameter configuration for Bio-Signal & Telemetry Anomaly Detection module.

This module defines global constants used for synthetic data generation, 
baseline thresholds, and ensemble model hyperparameters. These values 
are referenced symbolically in the thesis documentation via tags such as 
\\ref_ast{config.py:N_SAMPLES}.

Complexity:
    Space: O(1) constant memory overhead.
"""
from __future__ import annotations

# Data Generation Parameters
N_SAMPLES: int = 600
"""Total number of samples to generate for the synthetic bio-signal dataset."""

ANOMALY_RATIO: float = 0.08
"""Fraction of the dataset expected to be anomalous (0.0 to 1.0)."""

# Detection Thresholds
Z_THRESHOLD: float = 2.4
"""Z-score threshold for the static univariate baseline detection."""

# Ensemble Model Hyperparameters
ENSEMBLE_TREES: int = 25
"""Number of trees in the Adaptive Robust Mahalanobis-Ensemble detector."""
