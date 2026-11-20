"""Module implementing the static univariate Z-score baseline."""
import numpy as np
from typing import Optional

class UnivariateZScoreBaseline:
    """A simple baseline detector using mean and standard deviation per channel."""
    threshold: float
    mean_: Optional[np.ndarray]
    std_: Optional[np.ndarray]

    def __init__(self, threshold: float=3.0) -> None:
        """Initialize with a Z-score threshold.

        Args:
            threshold: Number of standard deviations to consider an anomaly.
        """
        self.threshold = threshold
        self.mean_ = None
        self.std_ = None

    def fit(self, X: np.ndarray) -> None:
        """Compute mean and standard deviation for each channel.

        Args:
            X: Training data of shape (n_samples, n_features).
        """
        self.mean_ = np.mean(X, axis=0)
        self.std_ = np.std(X, axis=0)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict anomalies based on Z-score.

        Args:
            X: Data to predict on of shape (n_samples, n_features).

        Returns:
            Boolean array indicating anomalies of shape (n_samples,).
        """
        if self.mean_ is None or self.std_ is None:
            raise RuntimeError('Model must be fitted before prediction')
        z_scores = np.abs(X - self.mean_) / (self.std_ + 1e-08)
        return np.any(z_scores > self.threshold, axis=1)
