"""Generates synthetic multi-channel physiological telemetry signals with injected anomalies for ground-truth evaluation."""
import numpy as np
from typing import Tuple

# Constants declared in specification
NUM_CHANNELS: int = 8
ANOMALY_PROBABILITY: float = 0.01
N_SAMPLES: int = 2000

def generate_dataset(seed: int) -> Tuple[np.ndarray, np.ndarray]:
    """Generate synthetic physiological data with anomalies and return the signal along with its ground-truth binary labels.

    Constructs a multi-channel time series where each channel follows a smooth stochastic process (sine with noise). Anomalies are injected randomly by adding a large offset.

    Parameters
    ----------
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        A tuple containing:
        - `data`: A numpy array of shape (N_SAMPLES, NUM_CHANNELS).
        - `labels`: A numpy array of shape (N_SAMPLES,) with binary values 0 or 1.

    Examples
    --------
    >>> data, labels = generate_dataset(seed=42)
    >>> data.shape
    (2000, 8)
    >>> labels.shape
    (2000,)
    >>> set(labels.tolist()).issubset({0, 1})
    True
    """
    rng = np.random.default_rng(seed)
    
    # Generate base signals: smooth stochastic processes (sine waves + noise) per channel
    data = np.zeros((N_SAMPLES, NUM_CHANNELS))
    t = np.linspace(0, 1, N_SAMPLES) * np.pi / 4  # Normalize time for frequency control
    
    for c in range(NUM_CHANNELS):
        # Simulate a physiological-like signal with different frequencies and phases
        freq = (c + 1) * 0.5  # Different frequencies per channel
        phase = c * 0.2
        data[:, c] = np.sin(t * freq + phase) + rng.normal(0, 0.1, N_SAMPLES)
    
    # Initialize labels as normal (0)
    labels = np.zeros(N_SAMPLES, dtype=int)
    anomaly_indices = rng.choice(N_SAMPLES, size=int(N_SAMPLES * ANOMALY_PROBABILITY), replace=False)
    
    # Inject anomalies: significant amplitude shift
    anomalous_amplitude = 3.0
    for idx in anomaly_indices:
        labels[idx] = 1
        for c in range(NUM_CHANNELS):
            # Random sign flip to mimic various artifact types
            data[idx, c] += rng.choice([-anomalous_amplitude, anomalous_amplitude])
    
    return data, labels