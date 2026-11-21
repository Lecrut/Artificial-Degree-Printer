"""Implements the proposed Random Subspace Ensemble detector for robust anomaly detection."""
import numpy as np
from typing import Optional

class RSADetector:
    """Random Subspace Ensemble anomaly detector.

    Fits on data by learning mean and standard deviation of random feature subspaces,
    then predicts anomalies based on standardized distance from these subspaces.
    """
    n_estimators: int
    random_state: Optional[int]
    estimators_: list[list[int]]
    mean_subspaces_: list[np.ndarray]
    std_subspaces_: list[np.ndarray]
    train_score_mean_: float
    train_score_std_: float

    def __init__(self, n_estimators: int=50, random_state: Optional[int]=None) -> None:
        """Initialize the detector with hyperparameters.

    Parameters
    ----------
    n_estimators : int
        Number of random subspaces to use.
    random_state : Optional[int]
        Seed for reproducibility.
    """
        self.n_estimators: int = n_estimators
        self.random_state: Optional[int] = random_state
        self.estimators_: list[list[int]] = []
        self.mean_subspaces_: list[np.ndarray] = []
        self.std_subspaces_: list[np.ndarray] = []
        self.train_score_mean_: float = 0.0
        self.train_score_std_: float = 0.0

    def fit(self, data: np.ndarray) -> 'RSADetector':
        """Fit the ensemble on training data.

Learns mean and standard deviation for each random subspace,
and stores statistics of anomaly scores computed on this training data
to allow automatic thresholding in `predict`.

Parameters
----------
data : np.ndarray
    Training data of shape (n_samples, n_features).

Returns
-------
RSADetector
    self
"""
        if self.random_state is not None:
            rng: np.random.RandomState = np.random.RandomState(self.random_state)
        else:
            rng = np.random.RandomState()
        n_samples, n_features = data.shape
        self.estimators_ = []
        self.mean_subspaces_ = []
        self.std_subspaces_ = []
        all_scores: list[float] = []
        for _ in range(self.n_estimators):
            n_subset: int = rng.randint(1, n_features + 1)
            indices: np.ndarray = rng.choice(n_features, size=n_subset, replace=False)
            self.estimators_.append(indices.tolist())
            X_sub = data[:, indices]
            mean_val: np.ndarray = np.mean(X_sub, axis=0)
            std_val: np.ndarray = np.std(X_sub, axis=0, ddof=0)
            self.mean_subspaces_.append(mean_val)
            self.std_subspaces_.append(std_val)
            std_safe: np.ndarray = np.maximum(std_val, 1e-08)
            diff: np.ndarray = (X_sub - mean_val) / std_safe
            score: np.ndarray = np.sum(diff ** 2, axis=1)
            all_scores.extend(score.tolist())
        self.train_score_mean_ = float(np.mean(all_scores))
        self.train_score_std_ = float(np.std(all_scores, ddof=0))
        return self

    def predict(self, data: np.ndarray) -> np.ndarray:
        """Predict anomalies (1) or normal (0) for the given data.

    Uses a threshold derived from training scores (mean + 3 * std)
    to determine binary prediction. Requires `fit` to have been called.

    Parameters
    ----------
    data : np.ndarray
        Data of shape (n_samples, n_features).

    Returns
    -------
    np.ndarray
        Integer array of shape (n_samples,).
    """
        if len(self.mean_subspaces_) == 0:
            raise ValueError('Detector must be fitted before predicting')
        scores: np.ndarray = self.predict_scores(data)
        threshold: float = self.train_score_mean_ + 3 * self.train_score_std_
        return (scores > threshold).astype(int)

    def predict_scores(self, data: np.ndarray) -> np.ndarray:
        """Compute continuous anomaly score for each sample.

    Returns an array of shape (n_samples,) with float values.

    Parameters
    ----------
    data : np.ndarray
        Data of shape (n_samples, n_features).

    Returns
    -------
    np.ndarray
        Array of shape (n_samples,).
    """
        if len(self.mean_subspaces_) == 0:
            raise ValueError('Detector must be fitted before predicting')
        n_samples: int = data.shape[0]
        total_scores: np.ndarray = np.zeros(n_samples, dtype=float)
        for j in range(len(self.estimators_)):
            indices = self.estimators_[j]
            if len(indices) == 0:
                continue
            subspace_mean: np.ndarray = self.mean_subspaces_[j]
            subspace_std: np.ndarray = self.std_subspaces_[j]
            X_sub: np.ndarray = data[:, indices]
            std_safe: np.ndarray = np.maximum(subspace_std, 1e-08)
            diff: np.ndarray = (X_sub - subspace_mean) / std_safe
            score: np.ndarray = np.sum(diff ** 2, axis=1)
            total_scores += score
        return total_scores
