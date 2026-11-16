import numpy as np
from src.data_types import SignalSample, DetectionResult
from typing import List
import sys

class ZScoreBaseline:
    """Static univariate Z-score baseline for anomaly detection."""

    def __init__(self, threshold: float=3.0) -> None:
        self.threshold = threshold

    def fit(self, samples: List[SignalSample]) -> None:
        """Compute global mean and standard deviation from all samples.

        Args:
            samples: A list of SignalSample objects to compute statistics from.
        """
        all_values = []
        for sample in samples:
            all_values.extend(sample.channels.flatten())
        self.mean = np.mean(all_values)
        self.std = np.std(all_values)

    def predict(self, sample: SignalSample) -> DetectionResult:
        """Predict whether a single sample is anomalous based on z-score.

        Args:
            sample: A SignalSample to classify.

        Returns:
            DetectionResult: Object containing the anomaly flag and score.
        """
        scores = []
        if self.std == 0:
            return DetectionResult(is_anomaly=False, score=0.0)
        for ch in sample.channels.flatten():
            z_score = abs(ch - self.mean) / self.std
            scores.append(z_score)
        max_z_score = max(scores)
        is_anomaly = max_z_score > self.threshold
        return DetectionResult(is_anomaly=is_anomaly, score=float(max_z_score))
