"""Implementation of the Random Subspace Ensemble (RSE) detector for anomaly detection."""
import numpy as np
from typing import Optional, Sequence
from scipy.stats import multivariate_normal
_DEFAULT_N_ESTIMATORS: int = 50
default_subsample_ratio: float = 0.8

class RandomSubspaceDetector:
    """An ensemble anomaly detector that trains on random feature subspaces.

    Each base estimator captures the local statistics (mean and covariance/chol)
    of a random subset of features. Anomaly scores are derived from the ensemble
    aggregation (e.g., mean or max of negative log-likelihoods or Mahalanobis distances).

    The `predict` method returns continuous anomaly scores where higher values
    indicate greater likelihood of being an anomaly.
    """
    n_estimators: int
    subsample_ratio: float
    score_aggregation: str
    random_state: Optional[int]
    _estimators_: list

    def __init__(self, n_estimators: int=_DEFAULT_N_ESTIMATORS, subsample_ratio: float=default_subsample_ratio, score_aggregation: str='mean', random_state: Optional[int]=None):
        """Initialize the detector.

        Args:
            n_estimators: Number of random subspaces (base estimators) to train.
            subsample_ratio: Fraction of total features to sample for each estimator.
            score_aggregation: Method to combine per-estimator scores ('mean', 'max', 'median').
            random_state: Seed for reproducibility of subspace selection.
        """
        self.n_estimators = n_estimators
        self.subsample_ratio = subsample_ratio
        self.score_aggregation = score_aggregation
        self.random_state = random_state
        self._estimators_ = []

    def fit(self, X: np.ndarray) -> None:
        """Fit the detector on training data.

        Computes global normalization parameters (mean and std) for each feature
        based on the training set. Then, it generates random subspaces of features
        and computes local statistics (mean and covariance/chol) for each subspace.

        Args:
            X: Training data array of shape (n_samples, n_features).
               Must contain finite numeric values.
        """
        rng = np.random.default_rng(self.random_state)
        global_mean = X.mean(axis=0)
        n_samples, n_features = X.shape
        self._estimators_ = []
        for i in range(self.n_estimators):
            n_subset = int(n_features * self.subsample_ratio)
            subspace_indices = rng.choice(n_features, size=n_subset, replace=False)
            indices_sorted = np.sort(subspace_indices)
            X_subset = X[:, indices_sorted]
            mean_subset = X_subset.mean(axis=0)
            std_subset = X_subset.std(axis=0) + 1e-08
            self._estimators_.append({'mean': global_mean[indices_sorted], 'std': std_subset, 'indices': indices_sorted})

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Compute anomaly scores for samples.

        For each sample in X, calculates a distance or likelihood-based score
        relative to the fitted distribution on each random subspace. These
        individual scores are aggregated according to `score_aggregation`.

        The returned values are continuous non-negative floats. Higher scores
        indicate higher anomaly likelihood.

        Args:
            X: Data array of shape (n_samples, n_features) to score.

        Returns:
            Anomaly scores array of shape (n_samples,) with dtype float64.
            Values are >= 0.0. The scale depends on the magnitude of features
            and number of estimators, but represents relative anomaly strength.
        """
        n_samples, n_features = X.shape
        scores_list = []
        for estimator in self._estimators_:
            indices = estimator['indices']
            z_scores = np.zeros((n_samples, len(indices)))
            for i in range(n_samples):
                diff = X[i, indices] - estimator['mean']
                std_vals = estimator['std']
                std_vals_safe = np.where(std_vals > 1e-08, std_vals, 1e-08)
                z_scores[i] += np.abs(np.dot(diff, std_vals_safe) / std_vals)
            individual_score = z_scores.mean(axis=0).mean()
            if self.score_aggregation == 'max':
                scores_list.append(individual_score.max())
            elif self.score_aggregation == 'median':
                scores_list.append(np.median(individual_score))
            else:
                scores_list.append(individual_score.mean())
        if len(scores_list) == 1:
            return np.array([scores_list[0]], dtype=np.float64)
        elif self.score_aggregation == 'max':
            return np.max(scores_list, axis=0)
        elif self.score_aggregation == 'median':
            return np.median(scores_list, axis=0)
        else:
            return np.mean(scores_list, axis=0)
