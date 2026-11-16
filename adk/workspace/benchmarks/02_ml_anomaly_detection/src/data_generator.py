"""Synthetic multi-channel bio-signal telemetry generator."""
from __future__ import annotations
from src.config import get_anomaly_rate, get_noise_levels, get_seeds, get_data_dir, get_channels
from typing import List, Optional
import numpy as np
from src.config import get_anomaly_rate, get_noise_levels, get_seeds, get_data_dir
from src.data_types import SignalSample, DetectionResult

def generate_sample(channel: str, noise_level: float, anomaly_rate: float, seed: int) -> SignalSample:
    """Generate a single synthetic bio-signal sample with specified noise and anomaly rate.

    Args:
        channel: Identifier of the bio-signal channel (e.g., 'EEG', 'ECG').
        noise_level: Multiplicative factor for Gaussian additive noise.
        anomaly_rate: Probability of injecting an anomalous segment.
        seed: Random seed for reproducibility.

    Returns:
        A SignalSample with timestamps, channels, labels, and optional anomaly flags.
    """
    n_channels = len(get_channels())
    n_points = 100
    duration = 2.5
    rng = np.random.default_rng(seed)
    base_signal = np.zeros(n_points)
    if noise_level > 0:
        base_signal += rng.normal(loc=0, scale=noise_level, size=n_points)
    is_anomaly = bool(rng.random() < anomaly_rate)
    labels = np.zeros(n_points, dtype=int)
    anomaly_indices: List[int] = []
    n_anomalies_expected = max(1, int(round(anomaly_rate * len(labels))))
    available_slots = list(range(len(labels)))
    rng.shuffle(available_slots)
    selected_indices = available_slots[:n_anomalies_expected]
    for idx in selected_indices:
        if 0 <= idx < len(labels):
            labels[idx] = 1
            anomaly_indices.append(idx)
    return SignalSample(timestamps=np.linspace(0, duration, n_points), channels=base_signal, labels=labels, anomaly_indices=np.array(anomaly_indices, dtype=int))

def generate_dataset(channels: List[str], noise_levels: List[float], n_samples: int, seeds: List[int]) -> List[SignalSample]:
    """Generate a full dataset combining multiple channels and noise levels.

    Args:
        channels: List of channel identifiers to include in the dataset.
        noise_levels: List of noise factors to apply across samples.
        n_samples: Total number of samples to generate.
        seeds: List of random seeds for reproducibility.

    Returns:
        A list of SignalSample objects.
    """
    anomaly_rate = get_anomaly_rate()
    samples: List[SignalSample] = []
    rng_global = np.random.default_rng(42)
    for i in range(n_samples):
        channel_id = channels[i % len(channels)]
        noise_factor = noise_levels[i % len(noise_levels)]
        sample_seed = get_seeds()[i] if i < len(get_seeds()) else 42 + i * 1000
        sample_rng = np.random.default_rng(sample_seed)
        sample = generate_sample(channel=channel_id, noise_level=noise_factor, anomaly_rate=anomaly_rate, seed=int(sample_rng.integers(0, 2 ** 31)))
        samples.append(sample)
    return samples

def generate_dataset(channels: List[str], noise_levels: List[float], n_samples: int, seeds: List[int]) -> List[SignalSample]:
    """Generate a full dataset combining multiple channels and noise levels.

    Args:
        channels: List of channel identifiers to include in the dataset.
        noise_levels: List of noise factors to apply across samples.
        n_samples: Total number of samples to generate.
        seeds: List of random seeds for reproducibility.

    Returns:
        A list of SignalSample objects.
    """
    anomaly_rate = get_anomaly_rate()
    samples: List[SignalSample] = []
    rng_global = np.random.default_rng(42)
    for i in range(n_samples):
        channel_id = channels[i % len(channels)]
        noise_factor = noise_levels[i % len(noise_levels)]
        sample_seed = get_seeds()[i] if i < len(get_seeds()) else 42 + i * 1000
        sample_rng = np.random.default_rng(sample_seed)
        sample = generate_sample(channel=channel_id, noise_level=noise_factor, anomaly_rate=anomaly_rate, seed=int(sample_rng.integers(0, 2 ** 31)))
        samples.append(sample)
    return samples
