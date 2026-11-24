"""Module providing the Random Subspace Ensemble anomaly detector."""
from typing import Union
import numpy as np

class RandomSubspaceEnsemble:
    """An ensemble of anomaly detectors operating on random feature subspaces.

    Each estimator computes an anomaly score on a randomly selected subset of
    dimensions. The aggregate score across all estimators determines the final
    anomaly assessment.

    This class exposes two distinct outputs: raw continuous scores via
    ``get_anomaly_scores`` for metrics like AUC and binary predictions via
    ``detect`` for metrics like F1-score, preventing data type loss or semantic
    mismatch during evaluation.
    """

    def __init__(self, n_estimators: int, subspace_dim: int, threshold: float) -> None:
        """Initialize the ensemble with configuration parameters.

Args:
    n_estimators: The number of random subspaces (estimators) to create.
    subspace_dim: The dimensionality of each random subspace. Must be <=
        the number of features in the data passed to fit().
    threshold: The global decision threshold applied during detect().
        Scores strictly greater than this value are classified as
        anomalies (1), others as normal (0).
"""
        self.n_estimators: int = n_estimators
        self.subspace_dim: int = subspace_dim
        self.threshold: float = threshold
        self._estimators: list = []

    def fit(self, data: np.ndarray) -> None:
        """Train the ensemble on physiological telemetry data.

For each of the n_estimators estimators, a random subspace of size
subspace_dim is selected from the input data's feature dimensionality.
Internal statistics (e.g., mean and variance for that subspace) are
computed and stored as private attributes. Assumes input data is suitable
for statistical modeling (e.g., normalized or zero-mean).

Args:
data: A numpy array of shape (n_samples, n_features) containing
    multi-channel physiological time-series data.
"""
        n_features: int = data.shape[1]
        if self.subspace_dim > n_features:
            raise ValueError(f'subspace_dim ({self.subspace_dim}) must be <= n_features ({n_features})')
        for _i in range(self.n_estimators):
            mask: np.ndarray = np.random.choice(n_features, size=self.subspace_dim, replace=False)
            estimator: dict = {'mask': np.array(sorted(mask), dtype=np.int64), 'mean': np.zeros(self.subspace_dim), 'variance': np.zeros(self.subspace_dim)}
            X_sub: np.ndarray = data[:, mask]
            estimator['mean'] = np.mean(X_sub, axis=0)
            estimator['variance'] = np.var(X_sub, axis=0)
            self._estimators.append(estimator)

    def get_anomaly_scores(self, data: np.ndarray) -> np.ndarray:
        """Compute raw continuous anomaly scores for the input data.

Projects the input data onto each estimator's learned subspace,
computes an anomaly score for that subspace (e.g., distance to mean),
and aggregates these scores (e.g., by averaging). This method returns
the pre-thresholded values required for metric computation such as AUC.

Args:
    data: A numpy array of shape (n_samples, n_features) identical in
        feature dimensionality to the data used during fit().

Returns:
    A numpy array of shape (n_samples,) containing continuous anomaly
    scores. Higher values indicate higher likelihood of being anomalous.
"""
        if len(self._estimators) == 0:
            raise RuntimeError('Model has not been fitted yet.')
        all_scores: list[np.ndarray] = []
        for estimator in self._estimators:
            X_sub: np.ndarray = data[:, estimator['mask']]
            diff: np.ndarray = X_sub - estimator['mean']
            std: np.ndarray = np.sqrt(estimator['variance'] + 1e-08)
            diff_normalized: np.ndarray = diff / std
            score: np.ndarray = np.sum(diff_normalized ** 2, axis=1)
            all_scores.append(score)
        aggregated_scores: np.ndarray = np.mean(all_scores, axis=0)
        return aggregated_scores

    def detect(self, data: np.ndarray) -> np.ndarray:
        """Detect anomalies in the input data using the fitted ensemble.

Computes raw anomaly scores via ``get_anomaly_scores`` and compares them
against the threshold defined at initialization. Scores strictly greater
than the threshold are classified as anomalies.

Args:
    data: A numpy array of shape (n_samples, n_features) identical in
        feature dimensionality to the data used during fit().

Returns:
    A binary mask of shape (n_samples,) with dtype np.int64 (or bool),
    where 1 indicates an anomaly and 0 indicates normalcy.
"""
        scores = self.get_anomaly_scores(data)
        return (scores > self.threshold).astype(np.int64)
