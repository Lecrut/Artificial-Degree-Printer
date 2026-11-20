"""Configuration constants for the anomaly detection experiment."""
import numpy as np
NUM_SAMPLES: int = 1000
NUM_CHANNELS: int = 5
NOISE_STD: float = 1.0
ANOMALY_RATE: float = 0.05
SEEDS: list[int] = [42, 43, 44]
RANDOM_STATE: int = 42
ZSCORE_THRESHOLD: float = 3.0
ROBUST_THRESHOLD: float = 3.0

def __init__() -> None:
    """Initialize configuration constants."""
    NUM_SAMPLES: int = 2000
    NUM_CHANNELS: int = 3
    NOISE_STD: float = 0.5
    ANOMALY_RATE: float = 0.1
    SEEDS: list[int] = [42, 43, 44]
    RANDOM_STATE: int = 42
    ZSCORE_THRESHOLD: float = 3.0
    ROBUST_THRESHOLD: float = 2.5
