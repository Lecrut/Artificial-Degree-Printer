import numpy as np
import pytest
import base_detector


def test_ZScoreDetector_init():
    """Test initialization with declared threshold parameter."""
    detector = base_detector.ZScoreDetector(threshold=2.0)
    assert isinstance(detector, base_detector.ZScoreDetector)
    # Verify the attribute declared in specification is set
    assert detector.threshold == 2.0


def test_ZScoreDetector_fit():
    """Test fit method sets internal state by verifying get_anomaly_scores works afterwards."""
    threshold = 2.5
    n_features = 10
    n_samples = 50
    # Use deterministic data generation for reproducibility within the test
    rng = np.random.RandomState(42)
    true_mean = np.zeros(n_features)
    data = rng.normal(true_mean, 1, (n_samples, n_features))
    
    fitted_model = base_detector.ZScoreDetector(threshold=threshold)
    # According to spec and previous failures, fit returns None
    result = fitted_model.fit(data)
    assert result is None
    
    # Verify state was set by checking get_anomaly_scores works without error
    scores = fitted_model.get_anomaly_scores()
    assert isinstance(scores, np.ndarray)
    assert scores.shape == (n_samples,)


def test_ZScoreDetector_predict():
    """Test predict method returns a tuple of (boolean array, float array) with correct shapes."""
    detector = base_detector.ZScoreDetector(threshold=2.0)
    n_samples = 50
    n_features = 10
    rng = np.random.RandomState(42)
    data = rng.normal(0, 1, (n_samples, n_features))
    detector.fit(data)
    
    # Call predict with the required 'threshold' argument from spec
    predictions = detector.predict(threshold=2.0)
    
    # Assert return type is a tuple
    assert isinstance(predictions, tuple)
    assert len(predictions) == 2
    
    # Unpack to check types and shapes
    anomaly_mask, scores = predictions
    
    # Assert first element is boolean array with correct shape
    assert isinstance(anomaly_mask, np.ndarray)
    assert anomaly_mask.dtype == bool
    assert anomaly_mask.shape == (n_samples,)
    
    # Assert second element is float array with correct shape
    assert isinstance(scores, np.ndarray)
    assert scores.dtype in [np.float32, np.float64]
    assert scores.shape == (n_samples,)


def test_ZScoreDetector_get_anomaly_scores_returns_correct_shape():
    """Test that get_anomaly_scores returns the scores from the last predict call."""
    detector = base_detector.ZScoreDetector(threshold=2.0)
    n_samples = 50
    n_features = 10
    rng = np.random.RandomState(42)
    data = rng.normal(0, 1, (n_samples, n_features))
    detector.fit(data)
    
    # Call predict to populate internal scores
    _, raw_scores = detector.predict(threshold=2.0)
    
    # get_anomaly_scores should return those same scores
    retrieved_scores = detector.get_anomaly_scores()
    
    assert np.allclose(raw_scores, retrieved_scores)


def test_ZScoreDetector_predict_deterministic_with_data():
    """Test that predict results are deterministic given the same data and threshold."""
    # Generate fixed data to ensure determinism doesn't rely on internal RNG state
    rng = np.random.RandomState(42)
    data = rng.normal(0, 1, (50, 10))
    
    detector1 = base_detector.ZScoreDetector(threshold=2.0)
    detector1.fit(data)
    pred1 = detector1.predict(threshold=2.0)

    detector2 = base_detector.ZScoreDetector(threshold=2.0)
    detector2.fit(data)
    pred2 = detector2.predict(threshold=2.0)

    assert np.array_equal(pred1[0], pred2[0])
    assert np.allclose(pred1[1], pred2[1])
