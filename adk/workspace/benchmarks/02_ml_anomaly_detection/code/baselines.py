"""Implements the static single-variate Z-score anomaly detection baseline."""

import numpy as np


class ZScoreDetector:
    """Static single-variate Z-score anomaly detector.

    >>> det = ZScoreDetector(threshold=2.0)
    >>> y_scores = det.predict_scores(np.array([[0], [1]]))
    >>> len(y_scores)
    2
    >>> isinstance(det.predict(np.array([[0], [1]])), np.ndarray)
    True
    """

    threshold: float

    def __init__(self, threshold: float = 3.0) -> None:
        """Initialize with a Z-score threshold for anomaly detection.

        Args:
            threshold: The maximum absolute Z-score to flag an anomaly (default 3.0).

        Returns:
            A configured detector instance.
        """
        self.threshold = threshold

    def predict_scores(self, data: np.ndarray) -> np.ndarray:
        """Return the maximum absolute Z-score across channels for each row.

        >>> import numpy as np
        >>> det = ZScoreDetector(threshold=3.0)
        >>> # Data: [[0], [2]]. Mean=1, Std=1. Z-scores: [|0-1|/1, |2-1|/1] = [1., 1.]
        >>> d = np.array([[0], [2]])
        >>> scores = det.predict_scores(d)
        >>> scores.tolist()
        [1.0, 1.0]
        """
        means: np.ndarray = np.mean(data, axis=0)
        stds: np.ndarray = np.std(data, axis=0, ddof=0)
        stds[stds == 0] = 1.0
        z_scores: np.ndarray = np.abs((data - means) / stds)
        return np.max(z_scores, axis=1)

    def predict(self, data: np.ndarray) -> np.ndarray:
        """Return binary anomaly labels for each row based on Z-scores.

        >>> import numpy as np
        >>> det = ZScoreDetector(threshold=2.0)
        >>> # Data: [[0], [0], [0], [10]]. Mean=2.5, Std=4.33. Z(10)=1.73 < 2.0 -> [0,0,0,0]
        >>> d = np.array([[0], [0], [0], [10]])
        >>> y = det.predict(d)
        >>> y.tolist()
        [0, 0, 0, 0]
        """
        scores: np.ndarray = self.predict_scores(data)
        return (scores > self.threshold).astype(int)
