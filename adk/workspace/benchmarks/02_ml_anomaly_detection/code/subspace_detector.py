"""Implements the random subspace ensemble anomaly detector using Z-scores on random projections."""
import numpy as np
from typing import Tuple, Optional
N_ESTIMATORS: int = 20
SUBSPACE_DIMENSION: int = 3

class RandomSubspaceDetector:
    """An anomaly detector that uses an ensemble of univariate Z-score detectors on random feature subspaces.

    This class implements the core logic for generating random projections, computing local Z-scores,
    and aggregating them to produce a global anomaly score. It relies on reference statistics (mean and
    standard deviation) derived from clean, normal data to ensure robust anomaly detection even when
    the input signal contains outliers.

    Attributes:
        ref_mean: Array of shape (n_features,) containing the mean of normal reference data.
        ref_std: Array of shape (n_features,) containing the standard deviation of normal reference data.
        ref_data: Array of shape (n_ref_samples, n_features) storing the fit data to enable scoring later.
    """

    def __init__(self, n_estimators: int=N_ESTIMATORS, subspace_dim: int=SUBSPACE_DIMENSION, seed: int=42) -> None:
        """Initialize the detector with ensemble parameters.

        Args:
            n_estimators: Number of random subspaces to use in the ensemble.
            subspace_dim: Number of features (channels) in each random subspace.
            seed: Random seed for reproducibility of subspace indices selection.
        """
        self.n_estimators: int = n_estimators
        self.subspace_dim: int = subspace_dim
        self.seed: int = seed
        self.ref_mean: Optional[np.ndarray] = None
        self.ref_std: Optional[np.ndarray] = None
        self.ref_data: Optional[np.ndarray] = None

    def fit(self, data: np.ndarray) -> None:
        """Fit the detector by setting reference statistics from normal data.

        Computes `ref_mean` and `ref_std` along axis 0. Stores `data` for use in scoring later.

        Args:
            data: A 2D numpy array of shape (n_ref_samples, n_features) representing normal reference data.
        """
        if not isinstance(data, np.ndarray) or len(data.shape) != 2:
            raise ValueError('Input data must be a 2D numpy array.')
        self.ref_data = data.copy()
        self.ref_mean = np.mean(self.ref_data, axis=0)
        self.ref_std = np.std(self.ref_data, axis=0)

    def get_anomaly_scores(self) -> np.ndarray:
        """Compute anomaly scores for the reference data stored during `fit` using the ensemble.

    For each time step in the stored `ref_data`, computes the median of Z-scores across `n_estimators`
    random subspaces. Each subspace's Z-score is the mean absolute Z-score of the features
    within that subspace relative to `ref_mean` and `ref_std`.

    Returns:
        A 1D numpy array of shape (n_samples,) containing the anomaly scores.
    """
        if self.ref_data is None or self.ref_mean is None or self.ref_std is None:
            raise ValueError('Model has not been fit yet.')
        n_estimators = self.n_estimators
        subspace_dim = self.subspace_dim
        rng = np.random.default_rng(self.seed)
        scores = []
        for _ in range(n_estimators):
            indices = rng.choice(self.ref_data.shape[1], size=subspace_dim, replace=False)
            subspace = self.ref_data[:, indices]
            z_scores = np.abs((subspace - self.ref_mean[indices]) / self.ref_std[indices])
            subspace_scores = np.mean(z_scores, axis=1)
            scores.append(subspace_scores)
        return np.median(scores, axis=0)

    def predict(self, threshold: float) -> np.ndarray:
        """Compute binary anomaly predictions for the stored reference data.

    Computes the ensemble anomaly scores using `get_anomaly_scores` and applies `threshold`
    to produce binary predictions (True if score > threshold).

    Args:
        threshold: The float threshold above which a sample is considered an anomaly.

    Returns:
        Binary predictions of shape (n_samples,), where True indicates an anomaly.
    """
        if self.ref_data is None or self.ref_mean is None or self.ref_std is None:
            raise ValueError('Model has not been fit yet.')
        scores = self.get_anomaly_scores()
        predictions: np.ndarray = (scores > threshold).astype(bool)
        return predictions
