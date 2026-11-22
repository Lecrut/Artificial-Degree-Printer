from method_rse import RandomSubspaceDetector, default_subsample_ratio
import numpy as np

def test_constant_default_subsample_ratio():
    """Test that the default constant exists and is a float."""
    assert isinstance(default_subsample_ratio, float)

class TestRandomSubspaceDetector:

    def setup_method(self):
        """Setup common fixtures for tests."""
        self.n_estimators = 10
        self.subsample_ratio = 0.8
        self.score_aggregation = 'mean'
        self.random_state = 42
        self.detector = RandomSubspaceDetector(n_estimators=self.n_estimators, subsample_ratio=self.subsample_ratio, score_aggregation=self.score_aggregation, random_state=self.random_state)

    def test_init_attributes(self):
        """Test that __init__ sets the declared attributes correctly."""
        assert self.detector.n_estimators == self.n_estimators
        assert self.detector.subsample_ratio == self.subsample_ratio
        assert self.detector.score_aggregation == self.score_aggregation
        assert self.detector.random_state == self.random_state

    def test_fit_sets_internal_state(self):
        """Test that fit populates internal state used for prediction."""
        np.random.seed(42)
        X_fit = np.random.randn(100, 10).astype(float)
        self.detector.fit(X_fit)

    def test_predict_returns_array(self):
        """Test that predict returns a numpy array of correct shape and dtype."""
        np.random.seed(42)
        X_fit = np.random.randn(100, 10).astype(float)
        self.detector.fit(X_fit)
        X_pred = np.random.randn(50, 10).astype(float)
        pred_output = self.detector.predict(X_pred)
        assert hasattr(pred_output, '__iter__'), 'Predict output should be array-like'
        pred_array = np.asarray(pred_output)
        assert pred_array.ndim == 1, f'Expected 1D array, got shape {pred_array.shape}'
        assert len(pred_array) == X_pred.shape[0], 'Length mismatch'
        assert pred_array.dtype == np.float64, f'Expected dtype float64, got {pred_array.dtype}'

    def test_predict_scores_positive(self):
        """Test that all predicted scores are non-negative."""
        np.random.seed(42)
        X_fit = np.random.randn(100, 10).astype(float)
        self.detector.fit(X_fit)
        X_pred = np.random.randn(50, 10).astype(float)
        pred_output = self.detector.predict(X_pred)
        assert np.all(pred_output >= 0), 'All predicted scores must be non-negative'
