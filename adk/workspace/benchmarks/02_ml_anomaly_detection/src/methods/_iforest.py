"""Isolation Forest detector trained on robust multi-feature statistics."""
from typing import List, Optional
from typing import List
from data_types import SignalSample, DetectionResult
import numpy as np
from sklearn.ensemble import IsolationForest
ENSEMBLE_SIZE = 10
CONTAMINATION_RATE = 0.05
RANDOM_STATE = 42
SEED_VALUE: int = RANDOM_STATE

class IForestEnsemble:
    """Isolation Forest detector trained on robust multi-feature statistics.

    Attributes:
        ensemble_size: Number of base estimators in the ensemble.
        contamination_rate: Expected proportion of anomalies in data.
    """

    def __init__(self, ensemble_size: int=ENSEMBLE_SIZE, contamination_rate: float=CONTAMINATION_RATE) -> None:
        """Initialize the Isolation Forest ensemble.

        Args:
            ensemble_size: Number of base estimators in the ensemble.
            contamination_rate: Expected proportion of anomalies in data.
        """
        self.ensemble_size: int = ensemble_size
        self.contamination_rate: float = contamination_rate
        self.iforest: IsolationForest | None = None
        self.threshold: float = 0.0

    def fit(self, samples: list) -> None:
        """Train the Isolation Forest on the provided samples.

        Args:
            samples: A list of SignalSample objects to train on.
        """
        from data_types import SignalSample
        if not samples:
            raise ValueError('No valid samples provided for training.')
        raw_ts_data: list = []
        combined_features: list = []
        for sample in samples:
            if hasattr(sample, 'timestamps') and len(sample.timestamps) > 0:
                ts_raw = np.array(sample.timestamps).flatten()
                raw_ts_data.append(ts_raw)
                combined_features.append(ts_raw)
            if hasattr(sample, 'channels'):
                for c_id, c_data in enumerate(sample.channels):
                    if c_data is not None and len(c_data) > 0:
                        ch_flat = np.array(c_data).flatten()
                        combined_features.append(ch_flat)
        if not combined_features:
            raise ValueError('No features extracted from samples.')
        X_matrix: np.ndarray = np.stack(combined_features, axis=0)
        self.iforest = IsolationForest(n_estimators=self.ensemble_size, contamination=self.contamination_rate, random_state=RANDOM_STATE)
        self.iforest.fit(X_matrix)
        sample_scores = self.iforest.score_samples(X_matrix[:5])
        self.threshold = float(np.percentile(sample_scores, (1 - self.contamination_rate) * 100))

    def predict(self, sample: SignalSample) -> DetectionResult:
        """Predict whether a single sample is anomalous.

        Args:
            sample: A SignalSample to classify.

        Returns:
            DetectionResult: Object containing the anomaly flag and score.
        """
        from data_types import DetectionResult, SignalSample
        if self.iforest is None:
            raise RuntimeError('Model has not been fitted yet')
        ch_features: list = []
        if hasattr(sample, 'timestamps') and len(sample.timestamps) > 0:
            ts_raw = np.array(sample.timestamps).flatten()
            combined_X = [ts_raw]
        else:
            combined_X = []
        if hasattr(sample, 'channels'):
            for c_id, c_data in enumerate(sample.channels):
                if c_data is not None and len(c_data) > 0:
                    ch_flat = np.array(c_data).flatten()
                    combined_X.append(ch_flat)
        if combined_X:
            X_input: np.ndarray = np.stack(combined_X, axis=0)
        else:
            raise ValueError('No features available for prediction.')
        pred_scores: np.ndarray = self.iforest.score_samples(X_input)
        score: float = float(np.mean(pred_scores))
        is_anomaly: bool = score > self.threshold
        return DetectionResult(score=score, is_anomaly=is_anomaly)
from sklearn.ensemble import IsolationForest
