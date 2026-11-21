"""Random Subspace Ensemble for anomaly detection."""
import numpy as np
from sklearn.ensemble import IsolationForest

class RandomSubspaceEnsemble:
    """Ensemble of Isolation Forests trained on random feature subspaces.
    
    Note: Scores follow sklearn convention: higher score = more normal, lower = more anomalous.
    """

    def __init__(self, n_estimators: int=100, subspace_size: int=None, contamination: float=0.1, seed: int=42) -> None:
        """Initialize the ensemble.

    Args:
        n_estimators: Number of base Isolation Forests.
        subspace_size: Number of features per estimator. If None, uses all features.
        contamination: Expected fraction of anomalies.
        seed: Random seed for reproducibility.
    """
        self.n_estimators = n_estimators
        self.subspace_size = subspace_size
        self.contamination = contamination
        self.seed = seed
        self.estimators_: list[IsolationForest] = []
        self.feature_indices_: list[np.ndarray] = []

    def fit(self, X: np.ndarray) -> None:
        """Fit the ensemble on normal data (X: shape [n_samples, n_features]).

    Note: This expects transposed input relative to generator output.
    Args:
        X: Shape (n_samples, n_features).
    """
        self.estimators_ = []
        self.feature_indices_ = []
        n_samples, n_features = X.shape
        subspace_size = self.subspace_size if self.subspace_size is not None else n_features
        rng = np.random.default_rng(self.seed)
        for i in range(self.n_estimators):
            indices = rng.choice(n_features, size=subspace_size, replace=False)
            self.feature_indices_.append(indices)
            estimator = IsolationForest(n_estimators=100, contamination=self.contamination, random_state=self.seed + i)
            X_sub = X[:, indices]
            estimator.fit(X_sub)
            self.estimators_.append(estimator)
        return self

    def predict_scores(self, X: np.ndarray) -> np.ndarray:
        """Return anomaly scores for each sample.

    Returns:
        scores (np.ndarray): Shape [n_samples]. Higher score = more normal, lower = more anomalous.
    """
        if not self.estimators_:
            raise RuntimeError('Model has not been fitted yet.')
        n_samples = X.shape[0]
        all_scores = np.zeros((len(self.estimators_), n_samples))
        for i, estimator in enumerate(self.estimators_):
            indices = self.feature_indices_[i]
            X_sub = X[:, indices]
            scores = estimator.decision_function(X_sub)
            all_scores[i] = scores
        return np.mean(all_scores, axis=0)

    def get_subspace_indices(self) -> list[np.ndarray]:
        """Return the feature indices used by each estimator."""
        return self.feature_indices_
