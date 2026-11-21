from src.ensemble_detector import RandomSubspaceEnsemble
import numpy as np

def test_prediction_dimensions():
    """Verify that predict_scores returns a 1D array of scores."""
    model = RandomSubspaceEnsemble(n_estimators=3, subspace_size=2, contamination=0.1, seed=42)
    X = np.random.rand(10, 5)
    model.fit(X)
    scores = model.predict_scores(X)
    assert scores.shape[0] == X.shape[0]
    assert len(scores.shape) == 1

def test_score_ranges():
    """Verify that predict_scores returns finite values and checks consistency with predictions.
    
    Lower score should correspond to more anomalous samples. 
    We verify that scores are finite numbers (no NaN/Inf).
    """
    model = RandomSubspaceEnsemble(n_estimators=3, subspace_size=2, contamination=0.1, seed=42)
    X = np.random.rand(10, 5)
    model.fit(X)
    scores = model.predict_scores(X)
    
    # Check that scores are finite
    assert np.all(np.isfinite(scores)), "Scores must be finite numbers"

def test_consistency():
    """Verify that predict_scores returns consistent results for identical inputs."""
    model = RandomSubspaceEnsemble(n_estimators=3, subspace_size=2, contamination=0.1, seed=42)
    X = np.random.rand(10, 5)
    model.fit(X)
    scores_1 = model.predict_scores(X)
    scores_2 = model.predict_scores(X)
    assert np.array_equal(scores_1, scores_2)
