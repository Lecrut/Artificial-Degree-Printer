"""Implements the Random Subspace Ensemble detector for robust anomaly detection in physiological telemetry."""
import numpy as np

class RandomSubspaceDetector:
    """An ensemble anomaly detector that fits multiple independent sub-models on random subsets of features."""
    n_subspaces: int
    subspace_dim: int
    _means: list[np.ndarray]
    _covariances: list[np.ndarray]
    _subspace_indices: list[np.ndarray]

    def __init__(self, n_subspaces: int, subspace_dim: int) -> None:
        """Initializes the detector with the specified ensemble parameters.

        Args:
            n_subspaces: The number of random subspaces (sub-models) to train.
            subspace_dim: The dimensionality of each random subspace.
        """
        self.n_subspaces = n_subspaces
        self.subspace_dim = subspace_dim
        self._means: list[np.ndarray] = []
        self._covariances: list[np.ndarray] = []
        self._subspace_indices: list[np.ndarray] = []

    def fit(self, data: np.ndarray) -> None:
        """Trains the ensemble on the provided physiological telemetry data.

    For each of the n_subspaces, it randomly selects subspace_dim features,
    computes the mean and covariance of that subset, and stores them.

    Args:
        data: A 2D numpy array (n_samples, n_features) containing the training telemetry data.
    """
        self._means = []
        self._covariances = []
        self._subspace_indices = []
        n_features: int = data.shape[1]
        rng: np.random.Generator = np.random.default_rng(42)
        for _ in range(self.n_subspaces):
            indices: np.ndarray = rng.choice(n_features, size=self.subspace_dim, replace=False)
            self._subspace_indices.append(indices)
            subspace_data: np.ndarray = data[:, indices]
            mean: np.ndarray = np.mean(subspace_data, axis=0)
            cov: np.ndarray = np.cov(subspace_data.T)
            if cov.ndim == 0:
                cov = np.array([[cov]])
            self._means.append(mean)
            self._covariances.append(cov)

    def predict(self, data: np.ndarray) -> np.ndarray:
        """Calculates anomaly scores for the input data based on the fitted ensemble.

    The final score is the average Mahalanobis distance squared across all subspaces.

    Args:
        data: A 2D numpy array (n_samples, n_features) containing the telemetry data to evaluate.

    Returns:
        A 1D numpy array of shape (n_samples,) with anomaly scores (higher means more anomalous).
    """
        scores: np.ndarray = np.zeros(data.shape[0])
        for i in range(self.n_subspaces):
            indices: np.ndarray = self._subspace_indices[i]
            mean: np.ndarray = self._means[i]
            cov: np.ndarray = self._covariances[i]
            subspace_data: np.ndarray = data[:, indices]
            diff: np.ndarray = subspace_data - mean
            try:
                inv_cov: np.ndarray = np.linalg.inv(cov)
                mahal: np.ndarray = np.sum(diff @ inv_cov * diff, axis=1)
            except np.linalg.LinAlgError:
                mahal = np.sum(diff ** 2, axis=1)
            scores += mahal
        return scores / self.n_subspaces
