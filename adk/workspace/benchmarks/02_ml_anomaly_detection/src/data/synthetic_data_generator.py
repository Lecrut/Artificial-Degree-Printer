"""Synthetic Data Generator for Multi-Channel Bio-Signal Telemetry."""
import numpy as np
from typing import Tuple, List
from dataclasses import dataclass

@dataclass
class SignalConfig:
    """Configuration for generating bio-signal telemetry."""
    frequency: float = 1.0
    amplitude: float = 1.0
    channel_count: int = 3

    def __init__(self, num_channels: int=3, sample_length: int=100, num_segments: int=5) -> None:
        """
    Initialize configuration for bio-signal telemetry generation.

    Args:
        num_channels (int): Number of signal channels.
        sample_length (int): Length of data per sample segment.
        num_segments (int): Number of data segments to generate.
    """
        self.num_channels = num_channels
        self.sample_length = sample_length
        self.num_segments = num_segments

@dataclass
class AnomalyConfig:
    """Configuration for injected anomalies."""
    type_: str = 'spike'
    intensity: float = 2.0
    duration_samples: int = 50
    start_index: int = 100

class BioSignalGenerator:
    """Generates synthetic multi-channel bio-signal telemetry with optional anomalies."""

    def __init__(self, config: SignalConfig, anomaly_config: AnomalyConfig, rng_seed: int=42):
        """Initializes the signal generator.

        Args:
            config: Signal parameters (frequency, amplitude, channels).
            anomaly_config: Parameters for injected anomalies.
            rng_seed: Random seed for reproducibility.
        """
        self.config = config
        self.anomaly_config = anomaly_config
        self.rng = np.random.default_rng(rng_seed)

    def generate_normal_sample(self, length: int) -> np.ndarray:
        """Generates a clean multi-channel normal signal.

        Returns:
            A 2D numpy array of shape (channel_count, length).
        """
        phases = self.rng.uniform(0, 2 * np.pi, size=self.config.channel_count)
        signal = np.zeros((self.config.channel_count, length))
        for c in range(self.config.channel_count):
            signal[c] = self.config.amplitude * np.sin(2 * np.pi * self.config.frequency * np.linspace(0, 1, length) + phases[c])
        return signal

    def generate_anomaly_sample(self, start_idx: int, length: int) -> Tuple[np.ndarray, str]:
        """Generates a signal with injected anomaly.

    Args:
        start_idx: Index where the anomaly begins.
        length: Total length of the signal segment to generate.

    Returns:
        A tuple (signal_array, anomaly_type) where signal_array is 2D numpy array and anomaly_type is string.
    """
        if start_idx < 0 or start_idx >= length:
            raise ValueError(f'Anomaly start index {start_idx} out of bounds [0, {length})')
        signal = self.generate_normal_sample(length)
        anomaly_start = max(0, min(start_idx, length - self.anomaly_config.duration_samples))
        duration = self.anomaly_config.duration_samples
        end_idx = anomaly_start + duration
        anomaly_type = self.anomaly_config.type_
        if anomaly_type == 'spike':
            for c in range(self.config.channel_count):
                t = np.arange(duration)
                gaussian_kernel = np.exp(-2 * (t - duration / 2) ** 2 / (duration / 4))
                spike_val = self.rng.normal(0, self.anomaly_config.intensity)
                signal[c][anomaly_start:end_idx] += spike_val * gaussian_kernel
        elif anomaly_type == 'drift':
            drift_rate = self.anomaly_config.intensity * 0.1
            for c in range(self.config.channel_count):
                signal[c][anomaly_start:end_idx] += np.linspace(0, drift_rate * duration, duration)
        elif anomaly_type == 'noise':
            noise_level = self.anomaly_config.intensity
            for c in range(self.config.channel_count):
                signal[c][anomaly_start:end_idx] += self.rng.normal(0, noise_level, size=duration)
        return (signal, anomaly_type)

    def generate_dataset(self, num_segments: int) -> Tuple[List[np.ndarray], List[str]]:
        """Generates a dataset of multiple segments with random anomalies.

        Args:
            num_segments: Number of signal segments to generate.

        Returns:
            A tuple (X, y) where X is list of 2D arrays and y is list of anomaly type strings.
        """
        data = []
        labels = []
        for _ in range(num_segments):
            length = self.rng.integers(100, 500)
            signal = self.generate_normal_sample(length)
            if self.rng.random() < 0.3:
                start = self.rng.integers(0, length - 20)
                injected_signal, anomaly_type = self.generate_anomaly_sample(start, length)
                signal = injected_signal
            data.append(signal)
            labels.append('normal' if 'spike' not in str(self.anomaly_config.type_) else anomaly_type)
        return (data, labels)
