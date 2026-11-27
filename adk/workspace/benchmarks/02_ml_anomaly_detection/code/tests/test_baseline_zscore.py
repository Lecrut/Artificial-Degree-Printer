import numpy as np
import pytest
from baseline_zscore import ZScoreDetector

class TestZScoreDetector:
    """Tests for the ZScoreDetector class."""

    def test_init_sets_window_size(self):
        """Test that __init__ correctly sets the window_size attribute."""
        detector = ZScoreDetector(window_size=10)
        assert detector.window_size == 10

    def test_predict_empty_data_returns_empty_array(self):
        """Test that predict returns an empty boolean array for empty input."""
        detector = ZScoreDetector(window_size=5)
        channel_data = np.array([]).reshape(0, 2)
        bool_result, _ = detector.predict(channel_data)
        assert isinstance(bool_result, np.ndarray)
        assert bool_result.shape == (0,)
        assert bool_result.dtype == bool
        assert len(bool_result) == 0

    def test_predict_window_larger_than_data_no_division_by_zero(self):
        """Test that predict handles window_size > data length without error."""
        detector = ZScoreDetector(window_size=10)
        channel_data = np.array([[1.0, 2.0], [1.1, 2.1], [1.2, 2.2]])
        bool_result, _ = detector.predict(channel_data)
        assert isinstance(bool_result, np.ndarray)
        assert bool_result.shape == (3,)
        assert bool_result.dtype == bool

    def test_predict_single_channel_constant_signal_no_anomalies(self):
        """Test that constant signal produces no anomalies."""
        detector = ZScoreDetector(window_size=5)
        channel_data = np.full((10, 1), 5.0)
        bool_result, _ = detector.predict(channel_data)
        assert isinstance(bool_result, np.ndarray)
        assert bool_result.shape == (10,)
        assert bool_result.dtype == bool
        assert not np.any(bool_result)

    def test_predict_anomaly_detected_in_any_channel(self):
        """Test that an anomaly in any channel flags the time step."""
        detector = ZScoreDetector(window_size=5)
        base = np.zeros((10, 2))
        base[:-1, 0] = np.random.randn(9)
        base[-1, 0] = 100.0
        bool_result, max_z_scores = detector.predict(base)
        assert isinstance(bool_result, np.ndarray)
        assert bool_result.shape == (10,)
        assert bool_result[-1] == True

    def test_predict_multidimensional_input_shape(self):
        """Test that predict preserves duration dimension for multi-channel input."""
        detector = ZScoreDetector(window_size=5)
        channel_data = np.random.randn(20, 4)
        bool_result, _ = detector.predict(channel_data)
        assert isinstance(bool_result, np.ndarray)
        assert bool_result.shape == (20,)

    def test_predict_low_variance_signal_no_false_positives(self):
        """Test that low variance signal does not produce false positives due to numerical noise."""
        detector = ZScoreDetector(window_size=5)
        channel_data = np.array([[1.0, 2.0], [1.0 + 1e-10, 2.0 + 1e-10], [1.0 + 2e-10, 2.0 + 2e-10], [1.0 + 3e-10, 2.0 + 3e-10], [1.0 + 4e-10, 2.0 + 4e-10], [1.0 + 5e-10, 2.0 + 5e-10]], dtype=np.float64)
        bool_result, _ = detector.predict(channel_data)
        assert isinstance(bool_result, np.ndarray)
        assert not np.any(bool_result)
