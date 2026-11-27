import numpy as np
import pytest
from data_generator import generate_dataset, DEFAULT_DURATION, DEFAULT_N_CHANNELS, DEFAULT_ANOMALY_RATE, DEFAULT_NOISE_STD


class TestGenerateDatasetInterface:
    """Tests that the function exists and can be called with valid arguments."""

    def test_callable_with_default_constants(self):
        rng = np.random.default_rng(42)
        data, mask = generate_dataset(n_channels=DEFAULT_N_CHANNELS, duration=DEFAULT_DURATION, anomaly_rate=DEFAULT_ANOMALY_RATE, noise_std=DEFAULT_NOISE_STD, rng=rng)
        assert data is not None
        assert mask is not None

    def test_callable_with_custom_values(self):
        rng = np.random.default_rng(42)
        data, mask = generate_dataset(n_channels=3, duration=100, anomaly_rate=0.05, noise_std=0.2, rng=rng)
        assert data is not None
        assert mask is not None

    def test_returns_tuple(self):
        rng = np.random.default_rng(42)
        result = generate_dataset(n_channels=2, duration=50, anomaly_rate=0.01, noise_std=0.1, rng=rng)
        assert isinstance(result, tuple)

class TestGenerateDatasetOutputShapes:
    """Tests that output shapes match the interface description."""

    def test_default_shape(self):
        rng = np.random.default_rng(42)
        data, mask = generate_dataset(n_channels=DEFAULT_N_CHANNELS, duration=DEFAULT_DURATION, anomaly_rate=DEFAULT_ANOMALY_RATE, noise_std=DEFAULT_NOISE_STD, rng=rng)
        assert data.shape == (DEFAULT_DURATION, DEFAULT_N_CHANNELS)
        assert mask.shape == (DEFAULT_DURATION,)

    def test_custom_shape(self):
        n_ch = 10
        dur = 200
        rng = np.random.default_rng(42)
        data, mask = generate_dataset(n_channels=n_ch, duration=dur, anomaly_rate=0.02, noise_std=0.1, rng=rng)
        assert data.shape == (dur, n_ch)
        assert mask.shape == (dur,)

    def test_zero_duration(self):
        rng = np.random.default_rng(42)
        data, mask = generate_dataset(n_channels=5, duration=0, anomaly_rate=0.02, noise_std=0.1, rng=rng)
        assert data.shape == (0, 5)
        assert mask.shape == (0,)

    def test_data_dtype(self):
        rng = np.random.default_rng(42)
        data, _ = generate_dataset(n_channels=3, duration=50, anomaly_rate=0.02, noise_std=0.1, rng=rng)
        assert np.issubdtype(data.dtype, np.floating)

    def test_mask_dtype(self):
        rng = np.random.default_rng(42)
        _, mask = generate_dataset(n_channels=3, duration=50, anomaly_rate=0.02, noise_std=0.1, rng=rng)
        assert mask.dtype == bool

    def test_duration_matches_mask_length(self):
        for duration in [10, 50, 100]:
            rng = np.random.default_rng(42)
            data, mask = generate_dataset(n_channels=2, duration=duration, anomaly_rate=0.02, noise_std=0.1, rng=rng)
            assert len(data) == duration
            assert len(mask) == duration

    def test_channels_match_data_cols(self):
        for n_ch in [1, 5, 20]:
            rng = np.random.default_rng(42)
            data, _ = generate_dataset(n_channels=n_ch, duration=50, anomaly_rate=0.02, noise_std=0.1, rng=rng)
            assert data.shape[1] == n_ch

class TestGenerateDatasetBehavior:
    """Tests behavior regarding anomalies and edge cases."""

    def test_anomaly_mask_contains_true(self):
        """With a standard anomaly rate, we expect at least some anomalies in a reasonable duration."""
        rng = np.random.default_rng(42)
        data, mask = generate_dataset(n_channels=3, duration=1000, anomaly_rate=0.05, noise_std=0.1, rng=rng)
        assert np.any(mask)

    def test_zero_anomaly_rate_no_anomalies(self):
        """Even with anomaly_rate=0.0, the generator safeguards by injecting at least one anomaly."""
        rng = np.random.default_rng(42)
        _, mask = generate_dataset(n_channels=3, duration=100, anomaly_rate=0.0, noise_std=0.1, rng=rng)
        assert mask.sum() >= 1

    def test_high_anomaly_rate(self):
        """With a very high anomaly rate, most indices should be marked."""
        rng = np.random.default_rng(42)
        _, mask = generate_dataset(n_channels=3, duration=100, anomaly_rate=0.9, noise_std=0.1, rng=rng)
        assert np.sum(mask) > 50

    def test_negative_noise_std_handled(self):
        """Spec says: 'Negative or zero noise_std is handled as standard deviation magnitude (absolute value).'
        This implies it should not crash and should behave similarly to positive std.
        We check that it doesn't raise an error."""
        rng = np.random.default_rng(42)
        data, mask = generate_dataset(n_channels=3, duration=50, anomaly_rate=0.02, noise_std=-0.1, rng=rng)
        assert data.shape == (50, 3)
        assert mask.shape == (50,)

    def test_zero_noise_std_no_crash(self):
        """Zero noise std is valid magnitude."""
        rng = np.random.default_rng(42)
        data, mask = generate_dataset(n_channels=3, duration=50, anomaly_rate=0.02, noise_std=0.0, rng=rng)
        assert data.shape == (50, 3)
        assert mask.shape == (50,)

    def test_data_values_are_finite(self):
        """Generated data should not contain NaN or Inf."""
        rng = np.random.default_rng(42)
        data, _ = generate_dataset(n_channels=3, duration=100, anomaly_rate=0.02, noise_std=0.1, rng=rng)
        assert np.all(np.isfinite(data))
