import pytest
from baseline_detector import BaselineZScore

def test_initialization_requires_positive_threshold() -> None:
    """Tests that __init__ enforces a positive threshold according to the interface."""
    with pytest.raises(ValueError):
        BaselineZScore(threshold=0.0)
    with pytest.raises(ValueError):
        BaselineZScore(threshold=-1.5)

def test_detection_returns_boolean_array() -> None:
    """Tests that detect returns a boolean array of shape (n_samples,)."""
    import numpy as np
    from baseline_detector import BaselineZScore
    detector = BaselineZScore(threshold=2.5)
    data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    result = detector.detect(data)
    assert isinstance(result, np.ndarray)
    assert result.dtype == bool
    assert result.shape == (5,)

def test_detection_handles_zero_std() -> None:
    """Tests that detect returns False for all entries when std is zero."""
    import numpy as np
    from baseline_detector import BaselineZScore
    detector = BaselineZScore(threshold=2.5)
    data = np.array([5.0, 5.0, 5.0])
    result = detector.detect(data)
    assert not any(result)
