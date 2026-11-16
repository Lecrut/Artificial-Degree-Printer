"""Core data types for signal processing."""
from typing import List, Optional
from typing import Optional
from typing import NamedTuple, List
import numpy as np

class SignalSample(NamedTuple):
    """Represents a multi-channel time-series sample."""
    timestamps: np.ndarray
    channels: np.ndarray
    labels: np.ndarray
    anomaly_indices: Optional[List[int]] = None

class DetectionResult(NamedTuple):
    """Result of detection for a single sample."""
    score: float
    is_anomaly: bool

class DetectionResult:
    """Result of detection for a single sample.

    Attributes:
        score: Anomaly score (float, higher is more anomalous).
        is_anomaly: Boolean flag indicating if the sample is an anomaly.
    """

    def __init__(self, score: float, is_anomaly: bool) -> None:
        """Initialize DetectionResult.

        Args:
            score: Computed anomaly score.
            is_anomaly: Boolean classification result.
        """
        self.score = score
        self.is_anomaly = is_anomaly
