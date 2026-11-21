import numpy as np
from baselines import ZScoreDetector

def test_ZScoreDetector_init():
    """Test initialization and attribute access."""
    # Arrange
    det = ZScoreDetector(threshold=1.5)
    
    # Assert
    assert det.threshold == 1.5, "Threshold attribute should match input value."

def test_ZScoreDetector_predict_scores():
    """Test predict_scores calculation using provided doctest example."""
    # Arrange
    det = ZScoreDetector(threshold=3.0)
    d = np.array([[0], [2]])
    
    # Act
    scores = det.predict_scores(d)
    
    # Assert
    expected = [1.0, 1.0]
    assert scores.tolist() == expected, f"Expected {expected}, got {scores.tolist()}."

def test_ZScoreDetector_predict():
    """Test predict binary labels using provided doctest example."""
    # Arrange
    det = ZScoreDetector(threshold=2.0)
    d = np.array([[0], [0], [0], [10]])
    
    # Act
    y = det.predict(d)
    
    # Assert
    expected = [0, 0, 0, 0]
    assert y.tolist() == expected, f"Expected {expected}, got {y.tolist()}."
