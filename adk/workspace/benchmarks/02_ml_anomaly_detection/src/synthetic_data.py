"""Module for generating synthetic multi-channel bio-signal telemetry with anomalies."""
import numpy as np
from typing import Tuple

class SyntheticDataset:
    """Generates synthetic time-series data with correlated noise and sparse anomalies."""
    n_samples: 'object'
    n_channels: 'object'
    noise_std: 'object'
    anomaly_rate: 'object'

    def __init__(self, n_samples: int, n_channels: int, noise_std: float, anomaly_rate: float) -> None:
        """Initialize dataset parameters.

    Args:
        n_samples: Total number of samples.
        n_channels: Number of signal channels.
        noise_std: Standard deviation for Gaussian noise.
        anomaly_rate: Fraction of samples that are anomalies.
    """
        self.n_samples = n_samples
        self.n_channels = n_channels
        self.noise_std = noise_std
        self.anomaly_rate = anomaly_rate
        self._rng_state = None

    def generate(self, seed: int) -> Tuple[np.ndarray, np.ndarray]:
        """Generate synthetic data and ground truth labels.

    Args:
        seed: Random seed for reproducibility.

    Returns:
        X: numpy array of shape (n_samples, n_channels) with noisy signal.
        y: numpy array of shape (n_samples,) with boolean flags (True if anomaly).
    """
        if self._rng_state is None:
            np.random.seed(seed)
            self._rng_state = np.random.get_state()
        base_signal = np.cumsum(np.random.randn(self.n_samples, self.n_channels) * self.noise_std)
        rng_backup = np.random.get_state()
        num_anomalies = int(self.n_samples * self.anomaly_rate)
        anomaly_indices = np.sort(np.random.choice(self.n_samples, size=num_anomalies, replace=False))
        y = np.zeros(self.n_samples, dtype=bool)
        for idx in anomaly_indices:
            ch_idx = int(np.random.uniform(0, self.n_channels))
            y[idx] = True
        np.random.set_state(rng_backup)
        np.random.seed(seed)
        X_clean = np.zeros((self.n_samples, self.n_channels))
        for i in range(self.n_samples):
            X_clean[i] = base_signal[i]
        num_anomalies = int(self.n_samples * self.anomaly_rate)
        if num_anomalies > 0:
            idx_list = np.random.choice(self.n_samples, size=num_anomalies, replace=False)
            for i in idx_list:
                ch = int(np.random.uniform(0, self.n_channels))
                X_clean[i, ch] += 3.0 * np.std(base_signal) + np.random.randn() * (self.noise_std * 5)
                y[i] = True
        return (X_clean, y)
