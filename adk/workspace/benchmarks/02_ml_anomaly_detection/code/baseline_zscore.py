"""Implements the static univariate Z-score based anomaly detection baseline for multi-channel physiological telemetry."""
import numpy as np
from typing import Any

class ZScoreDetector:
    """A detector that flags anomalies in multi-channel physiological data using a Z-score threshold computed over a rolling window for each channel."""
    window_size: int

    def __init__(self, window_size: int) -> None:
        """Initializes the detector with a fixed window size for local statistics calculation. The Z-score threshold is implicitly set to standard values (typically 3.0) as per the static baseline definition."""
        self.window_size = window_size

    def predict(self, data: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Predicts anomalies for a 2D array of multi-channel data.

Computes Z-scores using a rolling window of `window_size` independently for each channel. 
For each time step `i`, the Z-score is computed relative to the mean and standard deviation 
of the window of points *preceding* `i` (i.e., indices `[max(0, i-window_size):i]`).
A time step is flagged as an anomaly if its absolute Z-score exceeds 3.0 in ANY channel.

Args:
data: A numpy array of shape (duration, n_channels) containing the telemetry signals.

Returns:
bool_array: A boolean numpy array of shape (duration,) where True indicates a detected anomaly.
max_abs_z_scores: A float numpy array of shape (duration,) where each value is the maximum 
absolute Z-score across all channels for that time step.

Edge cases:
- If data is empty (duration 0), returns `(np.array([], dtype=bool), np.array([], dtype=float))`.
- If the window has fewer than 2 points, standard deviation is treated as infinity (Z-score 0) to avoid division by zero.
- If standard deviation is effectively zero (constant history), Z-score is 0."""
        duration: int = data.shape[0]
        if duration == 0:
            return (np.array([], dtype=bool), np.array([], dtype=float))
        bool_array: np.ndarray = np.zeros(duration, dtype=bool)
        max_abs_z_scores: np.ndarray = np.zeros(duration, dtype=float)
        n_channels: int = data.shape[1]
        for j in range(n_channels):
            channel_data: np.ndarray = data[:, j]
            z_scores_channel: np.ndarray = np.zeros(duration, dtype=float)
            for i in range(duration):
                start_idx: int = max(0, i - self.window_size)
                end_idx: int = i
                window_vals: np.ndarray = channel_data[start_idx:end_idx]
                w_len: int = len(window_vals)
                if w_len < 2:
                    z_scores_channel[i] = 0.0
                else:
                    mean_val: float = float(np.mean(window_vals))
                    std_val: float = float(np.std(window_vals, ddof=1))
                    if std_val < 1e-08:
                        z_scores_channel[i] = 0.0
                    else:
                        current_val: float = float(channel_data[i])
                        z_scores_channel[i] = (current_val - mean_val) / std_val
            abs_z_scores: np.ndarray = np.abs(z_scores_channel)
            np.maximum(max_abs_z_scores, abs_z_scores, out=max_abs_z_scores)
        bool_array = max_abs_z_scores > 3.0
        return (bool_array.astype(bool), max_abs_z_scores)
