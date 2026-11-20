"""Module implementing the robust multi-feature ensemble detector."""
import numpy as np
from typing import Optional

class RobustEnsembleDetector:
    """A robust detector using Median and MAD (Median Absolute Deviation) per channel."""
    threshold: 'object'
    median_: 'Optional[np.ndarray]'
    mad_per_channel_: 'Optional[np.ndarray]'

    def __init__(self, threshold: float=3.0) -> None:
        """Initialize the detector with a MAD-based threshold.

    Args:
        threshold: Multiplier for MAD to define the anomaly boundary.
    """
        self.threshold = float(threshold)
        self.median_: Optional[np.ndarray] = None
        self.mad_per_channel_: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray) -> None:
        """Compute robust statistics (median and per-channel MAD) for each channel.

    Args:
        X: Training data of shape (n_samples, n_features).
    """
        X = np.asarray(X)
        self.median_ = np.median(X, axis=0)
        deviations = np.abs(X - self.median_)
        self.mad_per_channel_ = np.median(deviations, axis=0)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict anomalies using robust distance.

    Args:
        X: Data to predict on of shape (n_samples, n_features).

    Returns:
        Boolean array indicating anomalies.
    """
        X = np.asarray(X)
        if self.median_ is None or self.mad_per_channel_ is None:
            raise RuntimeError('Model not fitted yet.')
        z_scores = (X - self.median_) / (self.mad_per_channel_ + 1e-06)
        aggregated_anomalies = np.sum(np.abs(z_scores), axis=1) > self.threshold
        return aggregated_anomalies.astype(bool)
