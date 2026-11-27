"""Generates synthetic multi-channel physiological telemetry data with injected anomalies and known ground truth labels."""
import numpy as np

DEFAULT_DURATION: int = 1000
DEFAULT_N_CHANNELS: int = 5
DEFAULT_ANOMALY_RATE: float = 0.02
DEFAULT_NOISE_STD: float = 0.1

def generate_dataset(n_channels: int, duration: int, anomaly_rate: float, noise_std: float, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Generates synthetic physiological signals with injected anomalies.

    Returns a tuple containing:
    1. `data`: A numpy array of shape (duration, n_channels) containing the synthetic telemetry signals.
    2. `anomaly_mask`: A boolean numpy array of shape (duration,) where True indicates an anomalous time step.
    """
    if duration <= 0:
        return (np.empty((0, n_channels)), np.array([], dtype=bool))
    
    t = np.linspace(0, 10 * np.pi, duration)
    data = np.zeros((duration, n_channels), dtype=float)
    for ch in range(n_channels):
        freq = 1.0 + (ch % 3) * 0.5
        phase = ch * np.pi / 4
        signal = np.sin(2 * np.pi * freq * t + phase)
        data[:, ch] = signal
    
    noise_std_abs = abs(noise_std)
    noise = rng.normal(0, noise_std_abs, data.shape)
    data += noise
    
    n_anomalies = int(duration * anomaly_rate)
    if n_anomalies < 1:
        n_anomalies = 1
    
    anomaly_indices = rng.choice(duration, size=n_anomalies, replace=False)
    anomaly_mask = np.zeros(duration, dtype=bool)
    anomaly_mask[anomaly_indices] = True
    
    for idx in anomaly_indices:
        n_affected = rng.integers(1, n_channels + 1)
        affected_channels = rng.choice(n_channels, size=n_affected, replace=False)
        for ch in affected_channels:
            sign = rng.choice([-1.0, 1.0])
            magnitude_base = 5.0 if noise_std_abs > 0 else 10.0
            spike_magnitude = sign * (magnitude_base + rng.uniform(0, 5)) * noise_std_abs
            data[idx, ch] += spike_magnitude
            
    return (data, anomaly_mask)
