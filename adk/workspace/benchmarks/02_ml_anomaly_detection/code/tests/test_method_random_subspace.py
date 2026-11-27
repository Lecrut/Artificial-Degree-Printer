import numpy as np
import pytest
from method_random_subspace import RandomSubspaceDetector


class TestRandomSubspaceDetector:
    """Tests for RandomSubspaceDetector against its declared interface."""

    def test_init_stores_attributes(self):
        """Verify __init__ sets n_subspaces and subspace_dim attributes."""
        detector = RandomSubspaceDetector(n_subspaces=5, subspace_dim=3)
        assert hasattr(detector, 'n_subspaces')
        assert hasattr(detector, 'subspace_dim')
        assert detector.n_subspaces == 5
        assert detector.subspace_dim == 3

    def test_fit_and_predict_output_shape(self):
        """Verify fit populates state and predict returns correct shape."""
        rng = np.random.default_rng(42)
        n_samples_train = 10
        n_features = 3
        train_data = rng.normal(size=(n_samples_train, n_features))

        detector = RandomSubspaceDetector(n_subspaces=3, subspace_dim=2)
        detector.fit(train_data)

        # Test data with different number of samples
        n_test_samples = 5
        test_data = rng.normal(size=(n_test_samples, n_features))

        scores = detector.predict(test_data)

        assert isinstance(scores, np.ndarray)
        assert scores.shape == (n_test_samples,)

    def test_predict_output_values_finite(self):
        """Verify predict output contains finite floats and is not empty."""
        rng = np.random.default_rng(42)
        data = rng.normal(size=(10, 5))

        detector = RandomSubspaceDetector(n_subspaces=2, subspace_dim=2)
        detector.fit(data)

        scores = detector.predict(data)

        assert not np.any(np.isnan(scores)), "Scores should not contain NaN values"
        assert np.all(np.isfinite(scores))

    def test_predict_higher_anomaly_for_outliers(self):
        """Verify that points further from the distribution have higher anomaly scores."""
        rng = np.random.default_rng(123)
        n_samples = 50
        n_features = 4
        train_data = rng.normal(loc=0, scale=1, size=(n_samples, n_features))

        detector = RandomSubspaceDetector(n_subspaces=5, subspace_dim=4)
        detector.fit(train_data)

        # Base case: points near the mean (0,0,0,0) should have lower scores than outliers
        center_point = np.zeros((1, n_features))
        outlier_point = np.full((1, n_features), 10.0)

        score_center = detector.predict(center_point)[0]
        score_outlier = detector.predict(outlier_point)[0]

        # Since the detector is trained on standard normal distribution,
        # points near the mean should be less anomalous than distant outliers.
        assert float(score_outlier) > float(score_center), \
            f"Outlier score {score_outlier} should be greater than center score {score_center}"