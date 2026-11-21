from src.baseline_zscore import ZScoreBaseline
import pytest
import numpy as np

def test_compute_scores_shape():
    """Test that compute_scores returns scores with correct shape matching input X.

    Input X is (n_channels, signal_length).
    Output scores must be (signal_length,).
    """
    z_score = ZScoreBaseline(window_size=3, threshold=2.5)
    X_np = np.random.rand(2, 100)
    scores = z_score.compute_scores(X_np)
    assert isinstance(scores, tuple), f'Expected tuple, got {type(scores)}'
    assert len(scores) == 2, f'Expected tuple length 2 (for 2 channels), got {len(scores)}'
    for i, s in enumerate(scores):
        assert hasattr(s, 'shape'), f'Expected scores[{i}] to have .shape attribute, got {type(s)}'
        assert s.shape == (100,), f'Expected scores[{i}] shape (100,), got {s.shape}'
