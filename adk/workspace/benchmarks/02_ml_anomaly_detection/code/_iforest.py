"""Isolation Forest Implementation for Multi-Channel Bio-Signal Anomaly Detection."""
from src.data_types import SignalSample, DetectionResult
from src.config import get_channels, get_noise_levels, get_anomaly_rate, get_ensemble_size, SEED_VALUE
import numpy as np
from typing import List
import sys
sys.path.append('src')
from data_types import SignalSample, DetectionResult
from config import get_channels, get_noise_levels, get_anomaly_rate, get_ensemble_size
from sklearn.ensemble import IsolationForest
SEED_VALUE: int = 42

class IForestEnsemble:
    """Isolation Forest detector trained on robust multi-feature statistics."""

    def __init__(self, ensemble_size: int=10, contamination_rate: float=0.05) -> None:
        """Initialize the Isolation Forest model.

    Args:
        ensemble_size: Number of base IsolationForest estimators (default 10).
        contamination_rate: Expected proportion of anomalies in training data.
    """
        from src.config import get_ensemble_size, get_seeds
        self.estimators_count = get_ensemble_size()
        SEEDS = get_seeds()
        self.seed_index: int = 0

    def fit(self, samples: List[dt.SignalSample]) -> None:
        """Fit the ensemble using robust feature statistics.

    Args:
        samples: List of SignalSample objects.
    """
        from src.config import get_channels
        from data_types import SignalSample
        import numpy as np
        if len(samples) == 0:
            return
        n_channels = len(get_channels())
        features: np.ndarray = []
        for sample in samples:
            channel_vals: List[np.ndarray] = []
            for ch_id in get_channels():
                if ch_id not in sample.channels:
                    continue
                vals = sample.timestamps[sample.channels == ch_id]
                channel_vals.append(vals)
            if len(channel_vals) == 0:
                features.append(np.zeros(2 * n_channels))
                continue
            for i, v_arr in enumerate(channel_vals):
                v_flat = v_arr.flatten()
                m_val: float = np.mean(v_flat)
                x_val: float = np.max(v_flat)
                features.append([m_val, x_val])
        if len(features) == 0:
            return
        global_features: np.ndarray = np.array(features)
        for _ in range(self.estimators_count):
            est: sklearn.ensemble.IsolationForest = sklearn.ensemble.IsolationForest(n_jobs=-1, contamination=contamination_rate, random_state=SEEDS[self.seed_index % len(SEEDS)])
            self.estimators.append(est)
            global_features_copy = global_features.copy()
            try:
                est.fit(global_features_copy)
                self.seed_index += 1
            except Exception:
                pass
        self.global_features: np.ndarray = global_features

    def predict(self, sample: dt.SignalSample) -> dt.DetectionResult:
        """Predict whether a sample is anomalous using the ensemble.

    Args:
        sample: A SignalSample to classify.

    Returns:
        DetectionResult: Object containing is_anomaly flag and anomaly score.
    """
        from data_types import SignalSample, DetectionResult
        from src.config import get_channels
        if len(self.estimators) == 0:
            return DetectionResult(is_anomaly=False, score=0.5)
        n_channels = len(get_channels())
        feature_vec: np.ndarray = []
        for ch_id in get_channels():
            if ch_id not in sample.channels:
                continue
            vals = sample.timestamps[sample.channels == ch_id]
            v_flat = vals.flatten()
            feature_vec.append(np.mean(v_flat))
            feature_vec.append(np.max(v_flat))
        if len(feature_vec) == 0 or self.global_features.shape[0] == 0:
            return DetectionResult(is_anomaly=False, score=0.5)
        pred_vec: np.ndarray = np.array(feature_vec)
        scores: List[float] = []
        for est in self.estimators:
            try:
                s = est.decision_function(pred_vec)
                scores.append(s)
            except Exception:
                pass
        if len(scores) == 0:
            return DetectionResult(is_anomaly=False, score=0.5)
        mean_score: float = np.mean(scores)
        is_anom: bool = mean_score > 0
        score_norm: float = (mean_score - -1) / 2
        return DetectionResult(is_anomaly=is_anom, score=score_norm)
