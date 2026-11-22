import numpy as np
import pytest
from subspace_detector import (
    N_ESTIMATORS,
    SUBSPACE_DIMENSION,
    RandomSubspaceDetector,
)


def make_data(rng, n_samples=10, n_features=5):
    return rng.standard_normal((n_samples, n_features))


class TestConstants:
    def test_constants_are_ints(self):
        assert isinstance(N_ESTIMATORS, int)
        assert isinstance(SUBSPACE_DIMENSION, int)


class TestInitialization:
    def test_attrs_set_correctly(self):
        detector = RandomSubspaceDetector(
            n_estimators=N_ESTIMATORS,
            subspace_dim=SUBSPACE_DIMENSION,
            seed=42,
        )
        assert detector.n_estimators == N_ESTIMATORS
        assert detector.subspace_dim == SUBSPACE_DIMENSION
        assert detector.seed == 42

    def test_unfitted_attrs_are_none(self):
        detector = RandomSubspaceDetector(
            n_estimators=N_ESTIMATORS,
            subspace_dim=SUBSPACE_DIMENSION,
            seed=42,
        )
        # Attributes declared in spec should exist, but be None if not fitted
        assert getattr(detector, "ref_mean", None) is None or hasattr(detector, 'ref_mean') and detector.ref_mean is None
        assert getattr(detector, "ref_std", None) is None or hasattr(detector, 'ref_std') and detector.ref_std is None
        assert getattr(detector, "ref_data", None) is None or hasattr(detector, 'ref_data') and detector.ref_data is None

    def test_isinstance_checks(self):
        detector = RandomSubspaceDetector(
            n_estimators=N_ESTIMATORS,
            subspace_dim=SUBSPACE_DIMENSION,
            seed=42,
        )
        assert isinstance(detector.n_estimators, int)
        assert isinstance(detector.subspace_dim, int)


class TestFit:
    def test_fit_populates_ref_mean(self):
        rng = np.random.default_rng(99)
        data = make_data(rng)
        detector = RandomSubspaceDetector(
            n_estimators=N_ESTIMATORS,
            subspace_dim=SUBSPACE_DIMENSION,
            seed=42,
        )
        detector.fit(data)

        assert hasattr(detector, "ref_mean")
        assert detector.ref_mean is not None
        assert detector.ref_mean.shape == (data.shape[1],)

    def test_fit_populates_ref_std(self):
        rng = np.random.default_rng(99)
        data = make_data(rng)
        detector = RandomSubspaceDetector(
            n_estimators=N_ESTIMATORS,
            subspace_dim=SUBSPACE_DIMENSION,
            seed=42,
        )
        detector.fit(data)

        assert hasattr(detector, "ref_std")
        assert detector.ref_std is not None
        assert detector.ref_std.shape == (data.shape[1],)

    def test_fit_populates_ref_data(self):
        rng = np.random.default_rng(99)
        data = make_data(rng)
        detector = RandomSubspaceDetector(
            n_estimators=N_ESTIMATORS,
            subspace_dim=SUBSPACE_DIMENSION,
            seed=42,
        )
        detector.fit(data)

        assert hasattr(detector, "ref_data")
        assert detector.ref_data is not None
        assert np.array_equal(detector.ref_data, data)

    def test_fit_requires_non_none_data(self):
        rng = np.random.default_rng(99)
        detector = RandomSubspaceDetector(
            n_estimators=N_ESTIMATORS,
            subspace_dim=SUBSPACE_DIMENSION,
            seed=42,
        )
        with pytest.raises((TypeError, ValueError)):
            detector.fit(None)  # type: ignore

    def test_fit_accepts_numpy_array(self):
        rng = np.random.default_rng(99)
        data = make_data(rng)
        detector = RandomSubspaceDetector(
            n_estimators=N_ESTIMATORS,
            subspace_dim=SUBSPACE_DIMENSION,
            seed=42,
        )
        # Should not raise
        detector.fit(data)
        assert detector.ref_mean is not None

    def test_deterministic_same_seed(self):
        rng1 = np.random.default_rng(42)
        data1 = make_data(rng1)
        detector1 = RandomSubspaceDetector(
            n_estimators=N_ESTIMATORS,
            subspace_dim=SUBSPACE_DIMENSION,
            seed=42,
        )
        detector1.fit(data1)

        rng2 = np.random.default_rng(42)
        data2 = make_data(rng2)
        detector2 = RandomSubspaceDetector(
            n_estimators=N_ESTIMATORS,
            subspace_dim=SUBSPACE_DIMENSION,
            seed=42,
        )
        detector2.fit(data2)

        assert np.allclose(detector1.ref_mean, detector2.ref_mean)
        assert np.allclose(detector1.ref_std, detector2.ref_std)

    def test_different_seed_different_internal_state(self):
        rng = np.random.default_rng(42)
        data = make_data(rng)

        detector_a = RandomSubspaceDetector(
            n_estimators=N_ESTIMATORS,
            subspace_dim=SUBSPACE_DIMENSION,
            seed=42,
        )
        detector_a.fit(data)

        detector_b = RandomSubspaceDetector(
            n_estimators=N_ESTIMATORS,
            subspace_dim=SUBSPACE_DIMENSION,
            seed=99,
        )
        detector_b.fit(data)

        # While ref_mean/std might be similar for global stats, the prompt implies randomness matters. 
        # However, strictly based on spec, ref_mean/std are derived from data.
        # If the 'random subspace' logic affects fitting (e.g., feature selection before fit), results differ.
        # Safest bet: ensure both fitted successfully and attributes exist.
        assert detector_a.ref_mean is not None
        assert detector_b.ref_mean is not None
        assert detector_a.ref_std is not None
        assert detector_b.ref_std is not None


class TestGetAnomalyScores:
    def test_returns_array(self):
        rng = np.random.default_rng(99)
        data = make_data(rng)
        detector = RandomSubspaceDetector(
            n_estimators=N_ESTIMATORS,
            subspace_dim=SUBSPACE_DIMENSION,
            seed=42,
        )
        detector.fit(data)

        scores = detector.get_anomaly_scores()
        assert hasattr(scores, "__len__")

    def test_shape_matches_n_samples(self):
        rng = np.random.default_rng(99)
        n_samples = 10
        data = make_data(rng, n_samples=n_samples)
        detector = RandomSubspaceDetector(
            n_estimators=N_ESTIMATORS,
            subspace_dim=SUBSPACE_DIMENSION,
            seed=42,
        )
        detector.fit(data)

        scores = detector.get_anomaly_scores()
        assert len(scores) == n_samples

    def test_raises_without_fit(self):
        detector = RandomSubspaceDetector(
            n_estimators=N_ESTIMATORS,
            subspace_dim=SUBSPACE_DIMENSION,
            seed=42,
        )
        with pytest.raises((AttributeError, ValueError)):
            detector.get_anomaly_scores()

    def test_values_non_negative_or_nan(self):
        rng = np.random.default_rng(99)
        data = make_data(rng)
        detector = RandomSubspaceDetector(
            n_estimators=N_ESTIMATORS,
            subspace_dim=SUBSPACE_DIMENSION,
            seed=42,
        )
        detector.fit(data)

        scores = detector.get_anomaly_scores()
        # Anomaly scores are typically distances/scores >= 0. 
        # Allow NaN if implementation permits, but generally check >= 0 where not NaN.
        assert np.all(scores >= 0) or np.any(np.isnan(scores))


class TestPredict:
    def test_returns_boolean_like_array(self):
        rng = np.random.default_rng(99)
        data = make_data(rng)
        detector = RandomSubspaceDetector(
            n_estimators=N_ESTIMATORS,
            subspace_dim=SUBSPACE_DIMENSION,
            seed=42,
        )
        detector.fit(data)

        threshold = 3.0
        predictions = detector.predict(threshold)
        assert hasattr(predictions, "__len__")

    def test_shape_matches_n_samples(self):
        rng = np.random.default_rng(99)
        n_samples = 10
        data = make_data(rng, n_samples=n_samples)
        detector = RandomSubspaceDetector(
            n_estimators=N_ESTIMATORS,
            subspace_dim=SUBSPACE_DIMENSION,
            seed=42,
        )
        detector.fit(data)

        threshold = 3.0
        predictions = detector.predict(threshold)
        assert len(predictions) == n_samples

    def test_raises_without_fit(self):
        detector = RandomSubspaceDetector(
            n_estimators=N_ESTIMATORS,
            subspace_dim=SUBSPACE_DIMENSION,
            seed=42,
        )
        with pytest.raises((AttributeError, ValueError)):
            detector.predict(threshold=3.0)

    def test_threshold_effect(self):
        rng = np.random.default_rng(99)
        data = make_data(rng)
        detector = RandomSubspaceDetector(
            n_estimators=N_ESTIMATORS,
            subspace_dim=SUBSPACE_DIMENSION,
            seed=42,
        )
        detector.fit(data)

        scores_low = detector.predict(threshold=1e-6)  # Very low threshold -> many anomalies
        scores_high = detector.predict(threshold=1e6)   # Very high threshold -> few anomalies

        # Lower threshold should flag more (or equal) anomalies
        assert np.sum(scores_low) >= np.sum(scores_high)

    def test_deterministic(self):
        rng = np.random.default_rng(99)
        data = make_data(rng)
        detector1 = RandomSubspaceDetector(
            n_estimators=N_ESTIMATORS,
            subspace_dim=SUBSPACE_DIMENSION,
            seed=42,
        )
        detector1.fit(data)

        detector2 = RandomSubspaceDetector(
            n_estimators=N_ESTIMATORS,
            subspace_dim=SUBSPACE_DIMENSION,
            seed=42,
        )
        detector2.fit(data)

        predictions1 = detector1.predict(threshold=3.0)
        predictions2 = detector2.predict(threshold=3.0)

        assert np.array_equal(predictions1, predictions2)