"""Generates synthetic multi-channel physiological telemetry with injected anomalies of known location for evaluation."""
import numpy as np
from typing import Tuple
NORMAL_CHANNELS: int = 4
ANOMALY_DURATION_SAMPLES: int = 10
ANOMALY_MAGNITUDE_FACTOR: float = 5.0
SAMPLE_LENGTH: int = 200

def generate_sample(n_channels: int) -> np.ndarray:
    """Generate a single sample of clean multi-channel physiological telemetry.

    Returns a 2D numpy array of shape (SAMPLE_LENGTH, n_channels) containing continuous signal data.
    Each channel is an independent synthetic signal composed of a periodic sinusoidal trend and
    additive Gaussian noise. No anomalies are injected; this represents the clean baseline state.
    """
    t = np.linspace(0, 4 * np.pi, SAMPLE_LENGTH)
    samples = []
    for _ in range(n_channels):
        signal = np.sin(t) + np.random.normal(0, 0.1, size=SAMPLE_LENGTH)
        samples.append(signal)
    return np.array(samples)

def generate_dataset(n_samples: int, n_anomalies: int, seed: int) -> Tuple[np.ndarray, np.ndarray]:
    """Generate a dataset of telemetry samples with injected anomalies and corresponding ground truth labels.

    Args:
        n_samples: Total number of time steps in the generated telemetry sequence.
        n_anomalies: Number of distinct anomaly bursts to inject into the sequence.
        seed: Random seed for reproducibility of data generation.

    Returns:
        A tuple (telemetry, labels) where:
        - telemetry is a 2D numpy array of shape (n_samples, NORMAL_CHANNELS) with float values.
        - labels is a 1D boolean array of shape (n_samples,) indicating anomaly locations,
          True if the time step is anomalous, False otherwise.
    """
    np.random.seed(seed)
    clean_data = generate_sample(n_channels=4)
    n_per_channel = len(clean_data) // 4
    anomalies_positions = []
    for _ in range(n_anomalies):
        max_start = n_samples - ANOMALY_DURATION_SAMPLES
        min_start = 0
        if max_start <= min_start:
            start_idx = min(0, max_start) if max_start < 0 else max_start
        else:
            start_idx = np.random.randint(min_start, max_start + 1)
        end_idx = start_idx + ANOMALY_DURATION_SAMPLES
        anomaly_indices = list(range(start_idx, end_idx))
        anomalies_positions.extend(anomaly_indices)
