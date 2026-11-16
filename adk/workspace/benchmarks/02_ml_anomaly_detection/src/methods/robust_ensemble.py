"""Multi-feature robust ensemble detector."""
from scipy.stats import zscore, median_abs_deviation
from typing import List, Any, Tuple
import scipy
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from scipy.stats import zscore
import src.data_types as dt
from typing import List, Any
import numpy as np
from src.data_types import SignalSample, DetectionResult

class RobustEnsemble:

    def __init__(self, ensemble_size: int=10, threshold: float=0.5) -> None:
        """Initialize the ensemble with specified number of base estimators and aggregation threshold.

        Args:
            ensemble_size: Number of base detectors to instantiate.
            threshold: Aggregation score threshold for anomaly detection (lower is more sensitive).
        """
        self.ensemble_size = ensemble_size
        self.threshold = threshold
        self._iforest = IsolationForest(n_estimators=3, contamination=0.1, random_state=None)
        self._lof = LocalOutlierFactor(n_neighbors=min(20, self.ensemble_size), contamination=0.1)
        self._zscore_stats = None

    def fit(self, samples: List[dt.SignalSample]) -> None:
        """Learn statistics from input samples and initialize base detectors.

    Args:
        samples: List of signal samples to learn from.
    """
        if not samples:
            self._zscore_stats = {'median': np.array([0.0]), 'mad': np.array([1.0])}
            return
        channel_data = [s.channels for s in samples]
        stacked = np.vstack(channel_data)
        medians = np.median(stacked, axis=0)
        mads = median_abs_deviation(stacked, axis=0)
        mads[mads < 1e-09] = 1.0
        self._zscore_stats = {'median': medians, 'mad': mads}
        self._iforest.fit(stacked)
        self._lof.fit(stacked)

    def predict(self, sample: dt.SignalSample) -> dt.DetectionResult:
        """Compute anomaly score for a single sample against stored statistics.

        Args:
            sample: The signal sample to evaluate.

        Returns:
            DetectionResult: Contains the aggregated anomaly score and binary decision.
        """
        if self._zscore_stats is None:
            raise RuntimeError('Detector has not been fitted yet.')
        median = self._zscore_stats['median']
        mad = self._zscore_stats['mad']
        z_scores = np.abs((sample.channels - median) / mad)
        max_z_score = float(np.max(z_scores))
        mean_z_score = float(np.mean(z_scores))
        if sample.channels.ndim == 1:
            features = sample.channels.reshape(1, -1)
        else:
            features = sample.channels
        try:
            iforest_decision = self._iforest.decision_function(features)
        except ValueError:
            iforest_decision = np.zeros((1,))
        lof_decision = self._lof.score_samples(features)
        iforest_norm = (iforest_decision + 1.0) / 2.0
        lof_norm = (lof_decision + 1.0) / 2.0
        ensemble_score = (max_z_score + mean_z_score + float(iforest_norm[0]) + float(lof_norm[0])) / 4.0
        is_anomaly = bool(ensemble_score > self.threshold)
        return dt.DetectionResult(score=float(ensemble_score), is_anomaly=is_anomaly)

    def fit_with_separation(self, samples: List[dt.SignalSample]) -> None:
        """Fit the detector with separation between normal and anomaly classes.

        This method fits the detectors separately using only normal or anomaly samples,
        ensuring that the decision boundary is learned from distinct distributions.

        Args:
            samples: A list of SignalSample objects to compute statistics from.
        """
        import numpy as np
        from scipy.stats import zscore, median_abs_deviation
        normal_samples = []
        anomaly_samples = []
        for sample in samples:
            if len(sample.labels) > 0:
                channel_data = [s.channels for s in sample.anomaly_indices[:]]
                is_anomaly_class = any((s.labels[0] == 1 for s in sample.anomaly_indices[:]))
                if not is_anomaly_class:
                    normal_samples.append(sample)
                else:
                    anomaly_samples.append(sample)
        if normal_samples:
            normal_stacked = np.vstack([s.channels for s in normal_samples])
            self._zscore_stats_normal = {'median': np.median(normal_stacked, axis=0), 'mad': median_abs_deviation(normal_stacked, axis=0)}
        else:
            self._zscore_stats_normal = None
        if anomaly_samples:
            anomaly_stacked = np.vstack([s.channels for s in anomaly_samples])
            self._iforest.fit(anomaly_stacked)
            self._lof.fit(anomaly_stacked)
        elif normal_samples:
            normal_stacked = np.vstack([s.channels for s in normal_samples])
            self._iforest.fit(normal_stacked)
            self._lof.fit(normal_stacked)
        else:
            all_stacked = np.vstack([s.channels for s in samples])
            self._iforest.fit(all_stacked)
            self._lof.fit(all_stacked)

def __init__(self, ensemble_size: int=10, threshold: float=0.5) -> None:
    """Initialize the multi-feature robust ensemble detector.

    Args:
        ensemble_size: Number of base estimators to use (default 10).
        threshold: Scoring threshold for anomaly flagging (default 0.5).
    """
    from scipy.stats import zscore
    self.estimators = [None] * ensemble_size
    self.threshold = float(threshold)

def fit(self, samples: List['dt.SignalSample']) -> None:
    """Train the ensemble by computing robust statistics from samples.

    Args:
        samples: A list of SignalSample objects to compute robust stats from.
    """
    import numpy as np
    all_values = []
    for s in samples:
        features = []
        for c_idx, channel in enumerate(s.channels):
            features.append(np.mean(s.timestamps[c_idx]))
        all_values.extend(features)
    self.global_mean = float(np.mean(all_values))
    robust_std = float(zscore(all_values, nan_policy='omit'))

def predict(self, sample: 'dt.SignalSample') -> 'dt.DetectionResult':
    """Predict anomaly using robust Z-score statistics.

    Args:
        sample: A SignalSample to classify.

    Returns:
        DetectionResult: Object containing the anomaly flag and score.
    """
    import numpy as np
    from scipy.stats import zscore
    if self.global_mean is None or self.robust_std is None or self.robust_std == 0:
        return dt.DetectionResult(is_anomaly=False, score=0.0)
    features = []
    for c_idx, channel in enumerate(sample.channels):
        feat = np.mean(sample.timestamps[c_idx])
        z = abs(feat - self.global_mean) / self.robust_std
        features.append(z)
    score = float(max(features))
    is_anomaly = bool(score > self.threshold)
    return dt.DetectionResult(is_anomaly=is_anomaly, score=score)
import scipy
