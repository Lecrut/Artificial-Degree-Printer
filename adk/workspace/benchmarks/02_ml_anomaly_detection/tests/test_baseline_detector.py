import pytest
from src.detectors.baseline_zscore import UnivariateZScoreDetector
import numpy as np

class TestUnivariateZScoreDetector:

    def test_normal_input_shape(self):
        """Verify detector output shape matches input dimensions when given normal data."""
        detector = UnivariateZScoreDetector(threshold=3.0)
        x = np.array([[1, 2, 3], [4, 5, 6]])
        anomalies, counts = detector.detect(x)
        assert len(anomalies) == len(x)
        assert isinstance(counts, (int, np.integer))

    def test_nan_handling(self):
        """Verify detector handles NaN values gracefully."""
        detector = UnivariateZScoreDetector(threshold=3.0)
        x_with_nan = np.array([[1, 2, np.nan]])
        with pytest.raises(ValueError) as exc_info:
            detector.detect(x_with_nan)
        assert 'NaN' in str(exc_info.value)

    def test_zero_value_handling(self):
        """Verify detector handles zero values correctly."""
        detector = UnivariateZScoreDetector(threshold=3.0)
        x_zeros = np.array([[0, 0, 0]])
        anomalies, counts = detector.detect(x_zeros)
        assert len(anomalies) == len(x_zeros)
        assert isinstance(anomalies, (np.ndarray, list))
