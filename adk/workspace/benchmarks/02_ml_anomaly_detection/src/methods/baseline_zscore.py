"""Static univariate Z-score baseline detector."""
from typing import List, Optional
from src.data_types import SignalSample, DetectionResult, np
from typing import Any, List
from typing import Any, List, Optional
from src.data_types import SignalSample, DetectionResult, float64
from typing import Any
from scipy.stats import zscore, median_abs_deviation
from typing import List
import src.data_types as dt
import data_types as dt
from typing import List, Any
import numpy as np
from src.data_types import SignalSample, DetectionResult

class ZScoreBaseline:
    """Static univariate Z-score baseline detector."""

    def __init__(self, threshold: float=3.0) -> None:
        """Initialize the baseline detector.

        Args:
            threshold: Threshold for anomaly detection (default 3.0).
        """
        self.threshold: float = threshold
        self.global_mean: Optional[List[float]] = None
        self.robust_std: Optional[List[float]] = None

    def fit(self, samples: List[dt.SignalSample]) -> None:
        """Compute the global mean and robust standard deviation of all features.

    Args:
        samples: A list of SignalSample objects to compute statistics from.
    """
        if not samples:
            self.global_mean = []
            self.robust_std = []
            return
        means: List[float] = []
        stds: List[float] = []
        for sample in samples:
            feature_values: List[float] = [float(sample.values[j]) for j in range(len(sample.channels))]
            m: float = np.mean(feature_values)
            s: float = np.median_abs_deviation(feature_values, scale=1.0) * 1.4826
            means.append(m)
            stds.append(s)
        self.global_mean = means
        self.robust_std = stds

    def predict(self, sample: object) -> object:
        """Predict whether a single sample is anomalous based on Z-score.

        Args:
            sample: A SignalSample to classify.

        Returns:
            DetectionResult: Object containing the anomaly flag and score.
        """
        if self.global_mean is None or self.robust_std is None:
            return DetectionResult(is_anomaly=True, score=99.9)
        if len(self.global_mean) == 0 or len(self.robust_std) == 0:
            return DetectionResult(is_anomaly=True, score=99.9)
        m: float = self.global_mean[0]
        s: float = self.robust_std[0]
        if s == 0:
            z_score: float = 0.0
        else:
            z_score: float = abs((float(sample.values[0]) - m) / s)
        is_anomaly: bool = z_score > self.threshold
        score: float = z_score if is_anomaly else 0.0
        return DetectionResult(is_anomaly=is_anomaly, score=score)
