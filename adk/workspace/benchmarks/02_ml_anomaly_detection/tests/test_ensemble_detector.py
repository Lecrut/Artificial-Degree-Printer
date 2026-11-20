import numpy as np
from src.ensemble_detector import RobustEnsembleDetector

def test_predict_known_outliers():
    """
    Test that per-channel normalization does not dominate due to scale differences.
    Verifies the behavior described in the specification:
    - Constant input -> MAD is 0, replaced by 1e-6
    - Predicts anomalies using robust distance
    """
    det = RobustEnsembleDetector(threshold=2.0)
    
    # Test case from specification: constant input
    X_train = np.array([[1.0, 1.0], [1.0, 1.0], [1.0, 1.0]])
    det.fit(X_train)
    
    # Test case from specification: outlier in one channel vs normal in both
    X_test = np.array([[10.0, 1.0], [1.0, 1.0]])
    pred = det.predict(X_test)
    
    assert isinstance(pred, np.ndarray), "Predict must return a numpy array"
    assert pred.shape == (2,), f"Expected shape (2,), got {pred.shape}"
    # Specification example: [True, False] for [[10, 1], [1, 1]]
    assert bool(pred[0]), "First sample [[10, 1]] should be detected as anomaly"
    assert not bool(pred[1]), "Second sample [[1, 1]] should NOT be detected as anomaly"
