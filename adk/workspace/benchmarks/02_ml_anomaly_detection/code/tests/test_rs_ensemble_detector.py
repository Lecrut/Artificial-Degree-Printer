import numpy as np
import pytest
from rs_ensemble_detector import RandomSubspaceEnsemble


class TestRandomSubspaceEnsemble:
    """Tests for the Random Subspace Ensemble anomaly detector."""

    def test_init_parameters(self):
        """Test instantiation works and stores state via behavior."""
        ensemble = RandomSubspaceEnsemble(n_estimators=5, subspace_dim=2, threshold=1.0)
        assert ensemble is not None

    def test_detect_threshold_logic(self):
        """Test that detect() strictly uses the threshold for binary classification.

        This test verifies the interface behavior: get_anomaly_scores returns
        a 1D array of shape (n_samples,) and detect() returns a binary mask
        of shape (n_samples,). It checks that detect() matches (scores > threshold).
        """
        np.random.seed(42)
        n_samples = 100
        n_features = 5

        # Create data with some variance
        data = np.random.randn(n_samples, n_features)

        ensemble = RandomSubspaceEnsemble(
            n_estimators=10,
            subspace_dim=n_features,
            threshold=0.5
        )

        ensemble.fit(data)

        scores = ensemble.get_anomaly_scores(data)
        predictions = ensemble.detect(data)

        # Verify shape and type based on interface specification
        assert scores.shape == (n_samples,), f"Expected scores shape {(n_samples,)}, got {scores.shape}"
        assert predictions.shape == (n_samples,), f"Expected predictions shape {(n_samples,)}, got {predictions.shape}"
        assert predictions.dtype in [np.int64, bool]

        # Verify the logic: score > threshold -> 1, else 0
        expected_predictions = (scores > 0.5).astype(np.int64)
        np.testing.assert_array_equal(predictions, expected_predictions)

    def test_get_anomaly_scores_shape(self):
        """Test that get_anomaly_scores returns the correct shape (n_samples,)."""
        n_samples = 20
        n_features = 5

        ensemble = RandomSubspaceEnsemble(
            n_estimators=5,
            subspace_dim=n_features,
            threshold=1.0
        )

        data = np.random.randn(n_samples, n_features)
        ensemble.fit(data)

        scores = ensemble.get_anomaly_scores(data)

        assert isinstance(scores, np.ndarray)
        # The interface specifies shape (n_samples,), not (1, n_features) or similar
        assert scores.shape == (n_samples,), f"Expected shape {(n_samples,)}, got {scores.shape}"

    def test_detect_output_type(self):
        """Test that detect() returns int64 or bool."""
        n_samples = 10
        n_features = 2

        ensemble = RandomSubspaceEnsemble(
            n_estimators=5,
            subspace_dim=n_features,
            threshold=1.0
        )

        data = np.random.randn(n_samples, n_features)
        ensemble.fit(data)

        predictions = ensemble.detect(data)

        assert predictions.dtype in [np.int64, bool]

    def test_fit_data_shape_constraint(self):
        """Test that fit() handles data shape correctly.

        The spec says subspace_dim <= n_features. We test valid case.
        Invalid cases might raise exceptions, but the spec doesn't explicitly
        mandate error handling for invalid inputs in __init__ or fit, just
        describes what they *do* if called correctly.
        """
        np.random.seed(42)
        n_samples = 10
        n_features = 5
        valid_data = np.random.randn(n_samples, n_features)

        ensemble = RandomSubspaceEnsemble(
            n_estimators=2,
            subspace_dim=3, # < n_features
            threshold=0.5
        )

        # fit() should return None or just complete
        result = ensemble.fit(valid_data)
        assert result is None
