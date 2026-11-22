"""Implements the static univariate Z-score baseline detector."""
import numpy as np
from typing import Tuple

class ZScoreDetector:
    """Static univariate anomaly detector based on Z-scores.

    This detector calculates the mean and standard deviation for each channel
    of the input telemetry data. It flags a sample as an anomaly if the
    absolute Z-score in *any* channel exceeds a fixed threshold.

    The detector is 'static' because its parameters (mean and std derived from
    the fitting data) do not update during detection.
    """

    def __init__(self, threshold: float=3.0) -> None:
        """Initialize the detector with a fixed Z-score threshold."""
        self.threshold: float = threshold
        self._fitted: bool = False
        self._mean: np.ndarray | None = None
        self._std: np.ndarray | None = None
        self._raw_data: np.ndarray | None = None
        self._max_z_scores: np.ndarray | None = None

    def fit(self, data: np.ndarray) -> None:
        """Fit the detector by calculating statistics from clean data.

        Computes the mean and standard deviation for each channel in the
        provided `data` array. These statistics are stored internally and
        used during the detection phase.

        Args:
            data (np.ndarray): A 2D numpy array of shape (n_samples, n_channels)
                containing clean telemetry data from which to derive the baseline statistics.
        """
        self._raw_data = np.copy(data)
        self._mean = np.mean(self._raw_data, axis=0)
        self._std = np.std(self._raw_data, axis=0)
        self._fitted = True

    def get_anomaly_scores(self) -> np.ndarray:
        """Retrieve the anomaly scores computed during the last `predict` call.

        If `predict` has not been called yet but the detector is fitted,
        returns a zero array of shape (n_samples,).

        Returns:
            (np.ndarray): A numpy array of shape (n_samples,) containing the maximum
                absolute Z-score per sample across all channels.
        """
        if not self._fitted or self._raw_data is None:
            return np.zeros(self._raw_data.shape[0])
        if self._max_z_scores is None:
            return np.zeros(len(self._raw_data))
        return self._max_z_scores.copy()

    def predict(self, threshold: float | None=None) -> Tuple[np.ndarray, np.ndarray]:
        """Detect anomalies in the data passed to the last `fit` call.

        Uses the data originally passed to `fit()` for detection. It does not
        accept new data as an argument because this detector is designed for
        a single pass over the dataset derived during initialization.

        Args:
            threshold (float | None): The Z-score threshold to use for this specific prediction
                run. If None, uses `self.threshold`.

        Returns:
            Tuple[np.ndarray, np.ndarray]:
                - predictions (np.ndarray): A 1D boolean numpy array of shape (n_samples,
                  True if the absolute Z-score in *any* channel exceeds the provided
                  threshold; otherwise False).
                - anomaly_scores (np.ndarray): A numpy array of shape (n_samples,) containing
                  the maximum absolute Z-score across all channels for each sample.
        """
        if not self._fitted or self._raw_data is None:
            raise RuntimeError('ZScoreDetector must be fitted before calling predict.')
        eff_threshold = threshold if threshold is not None else self.threshold
        safe_stds = np.where(self._std == 0, 1e-08, self._std)
        z_scores = np.abs((self._raw_data - self._mean) / safe_stds)
        self._max_z_scores = np.max(z_scores, axis=1)
        predictions = self._max_z_scores > eff_threshold
        return (predictions, self._max_z_scores.copy())
