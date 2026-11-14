"""Implements a static univariate Z-score baseline detector for anomaly detection."""
from typing import Tuple, List
import numpy as np

class UnivariateZScoreDetector:
    """Detects anomalies using a static univariate Z-score threshold."""

    def __init__(self, threshold: float=3.0):
        """Initialize the detector with a fixed Z-score threshold.

        Args:
            threshold: The Z-score value above which samples are flagged as anomalies.
        """
        self.threshold: float = threshold
        self._reference_stat: Tuple[float, float] | None = None

    def _compute_reference_stats(self, x: np.ndarray) -> Tuple[float, float]:
        """Compute mean and standard deviation of the input array.

        Args:
            x: The input sample (assumed to be non-anomalous). Returns tuple [mean, std].
        """
        return (np.mean(x), np.std(x))

    def _classify_sample(self, x: np.ndarray, mean_val: float, std_val: float) -> int:
        """Classify a sample as normal or anomaly based on Z-score.

    Args:
        x: The input sample to classify. Returns 1 for normal, -1 for anomaly.
    """
        if std_val == 0:
            return 1
        z_score = float(np.abs(x - mean_val) / std_val)
        return 1 if z_score < self.threshold else -1

    def _detect_segment(self, x: np.ndarray) -> List[int]:
        """Detect anomalies in a single segment.

        This method assumes the input is clean. In a robust ensemble, 
        reference stats would be updated dynamically or via cross-validation.
        Here we use the whole segment as the baseline.

        Args:
            x: The input signal segment (1D array). Returns list of anomaly labels per timestep.
        """
        mean_val, std_val = self._compute_reference_stats(x)
        return np.array([self._classify_sample(xi, mean_val, std_val) for xi in x])

    def detect(self, x: np.ndarray) -> Tuple[np.ndarray, int]:
        """Run the univariate Z-score detector on a single signal.

    Args:
        x: The input signal (1D numpy array). Returns tuple of [anomaly_labels, n_anomalies].
    """
        if not isinstance(x, np.ndarray):
            raise TypeError('Input must be a numpy ndarray')
        if len(x) < 2:
            return (np.array([1] * len(x)), 0)
        if np.any(np.isnan(x)):
            raise ValueError('Input contains NaN values')
        anomaly_labels: np.ndarray = self._detect_segment(x)
        n_anomalies: int = sum((abs(label) for label in anomaly_labels))
        return (anomaly_labels, n_anomalies)
