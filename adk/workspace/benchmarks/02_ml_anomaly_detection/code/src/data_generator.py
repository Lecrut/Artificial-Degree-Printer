"""Synthetic multi-channel physiological telemetry generation with anomaly injection."""
import numpy as np

def generate_signal(n_channels: int, signal_length: int, n_anomalies: int, seed: int=42) -> tuple[np.ndarray, list[dict]]:
    """Generate synthetic signal and anomaly ground truth.

    Args:
        n_channels (int): Number of input channels.
        signal_length (int): Length of the time dimension.
        n_anomalies (int): Number of anomalies to inject.
        seed (int): Random seed for reproducibility.

    Returns:
        X (np.ndarray): Shape (n_channels, signal_length). Normal values in [-1, 1].
        anomalies (list[dict]): List of dicts with keys 'channel', 'start', 'end' defining injected anomalies.
    """
    rng: np.random.Generator = np.random.default_rng(seed)
    X: np.ndarray = np.zeros((n_channels, signal_length))
    for c in range(n_channels):
        noise_level: float = rng.normal(0, 0.3)
        X[c, :] = np.sin(2 * np.pi * c / (signal_length + 1)) * 0.5 + noise_level
    anomaly_ranges: list[tuple[int, int]] = []
    anomalies_list: list[dict] = []
    attempts: int = 0
    max_attempts: int = n_anomalies * 100
    while len(anomaly_ranges) < n_anomalies and attempts < max_attempts:
        attempts += 1
        start: int = rng.integers(0, signal_length - 2)
        length: int = rng.integers(1, 4)
        end: int = start + length
        if end > signal_length:
            continue
        conflict: bool = False
        for sr, sl in anomaly_ranges:
            if not (end <= sr or start >= sl):
                conflict = True
                break
        if conflict:
            continue
        c_idx: int = rng.integers(0, n_channels)
        anomaly_val: float = rng.uniform(-3.0, -1.0) + 2.0
        X[c_idx, start:end] = anomaly_val
        anomaly_entry: dict = {'channel': c_idx, 'start': start, 'end': end}
        anomalies_list.append(anomaly_entry)
        anomaly_ranges.append((start, end))
    return (X, anomalies_list)

def get_ground_truth_mask(anomalies: list[dict], signal_length: int, n_channels: int) -> np.ndarray:
    """Convert anomaly definitions to a boolean mask.

    Args:
        anomalies (list[dict]): List of dicts with 'channel', 'start', 'end'.
        signal_length (int): Length of the time dimension.
        n_channels (int): Number of channels.

    Returns:
        mask (np.ndarray): Shape (n_channels, signal_length) flattened to 1D (C-order). True where anomaly exists.
    """
    mask: np.ndarray = np.zeros(n_channels * signal_length, dtype=bool)
    for a in anomalies:
        ch: int = a['channel']
        st: int = a['start']
        en: int = a['end']
        for t in range(st, en):
            mask[ch * signal_length + t] = True
    return mask
