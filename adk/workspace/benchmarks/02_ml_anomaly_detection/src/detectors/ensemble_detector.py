"""
Multi-feature robust ensemble detector for bio-signal telemetry.
Combines Z-score, IQR, and statistical distribution fitting features via weighted voting or consensus thresholding.
"""

from typing import List, Tuple, Union, Dict
import numpy as np
from dataclasses import dataclass
import networkx as nx

@dataclass
class EnsembleDetectorConfig:
    """Configuration for the ensemble detector."""
    zscore_weight: float = 0.4
    iqr_weight: float = 0.4
    mean_std_weight: float = 0.2
    min_severity_score: Union[float, int] = 1.5


class EnsembleDetector:
    """
    Detects anomalies in multi-channel bio-signals using a weighted ensemble of statistical features.
    Returns detection results as (segment_index, confidence) tuples sorted by severity.
    """
    def __init__(self, config: EnsembleDetectorConfig):
        self.config = config

    def _compute_zscore(self, segment: np.ndarray) -> float:
        """
        Compute Z-score relative to the training mean and standard deviation.
        Returns a raw score indicating deviation from normality.
        """
        return np.abs(np.mean(segment) - self.training_mean) / (self.training_std + 1e-9)

    def _compute_iqr_score(self, segment: np.ndarray) -> float:
        """
        Compute anomaly score based on deviation from median and interquartile range.
        """
        q1, q3 = np.percentile(segment, 25), np.percentile(segment, 75)
        iqr = q3 - q1
        if iqr == 0:
            return 0.0
        return np.abs(np.mean(segment) - np.median(segment)) / (iqr + 1e-9)

    def _compute_mean_std_score(self, segment: np.ndarray) -> float:
        """
        Compute anomaly score based on deviation from global mean and variance.
        """
        return np.var(segment) / self.training_var + abs(np.mean(segment) - self.training_mean)

    def detect_segments(
        self,
        segments: List[np.ndarray],
        training_stats: Dict[str, Union[float, float]],
    ) -> Tuple[List[Tuple[int, float]], np.ndarray]:
        """
        Evaluate each segment using the ensemble of features.
        
        Arguments:
            segments: A list of numpy arrays representing signal segments to be tested.
            training_stats: Dictionary containing training mean, std, var for feature computation.
        
        Returns:
            detections: A list of tuples (segment_index, confidence_score).
            scores_matrix: A 2D array of raw scores per segment, useful for visualization.
        """
        zscore_scores = [self._compute_zscore(seg) for seg in segments]
        iqr_scores = [self._compute_iqr_score(seg) for seg in segments]
        mean_std_scores = [self._compute_mean_std_score(seg) for seg in segments]

        combined_scores = [
            (
                zscore_scores[i] * self.config.zscore_weight +
                iqr_scores[i] * self.config.iqr_weight +
                mean_std_scores[i] * self.config.mean_std_weight
            )
            for i in range(len(segments))
        ]

        detections = []
        for i, score in enumerate(combined_scores):
            if score >= self.config.min_severity_score:
                detections.append((i, float(score)))
        
        # Sort by severity (descending) then by index (ascending)
        detections.sort(key=lambda x: (-x[1], x[0]))

        return detections, np.array(combined_scores)
