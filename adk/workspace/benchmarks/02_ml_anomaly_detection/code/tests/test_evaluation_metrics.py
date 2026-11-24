from evaluation_metrics import compute_f1, compute_auc
import numpy as np
import pytest

def test_compute_f1_signatures_and_edge_cases():
    """Tests verify the signature and edge case behavior of compute_f1 according to specification."""
    # Test 1: Normal case with both positive predictions and negatives
    y_true = np.array([True, True, False, False])
    y_pred = np.array([False, True, True, False])
    result = compute_f1(y_true, y_pred)
    assert isinstance(result, float), "Result must be a float"
    assert 0.0 <= result <= 1.0, "F1 score must be in [0, 1]"

    # Test 2: No true positives (precision=0, recall=0 -> F1=0)
    y_true = np.array([False, False, True, False])
    y_pred = np.array([False, False, False, False])
    result = compute_f1(y_true, y_pred)
    assert result == 0.0, "F1 should be 0 when no predictions are made"

    # Test 3: No false positives (precision=1, recall=1 -> F1=1) handled by internal logic
    y_true = np.array([False, False, True, True])
    y_pred = np.array([False, False, True, True])
    result = compute_f1(y_true, y_pred)
    assert result == 1.0, "F1 should be 1 when all predictions are perfect"

    # Test 4: Shape mismatch raises ValueError
    with pytest.raises(ValueError):
        compute_f1(np.array([True]), np.array([True, True]))

def test_compute_auc_signatures_and_edge_cases():
    """Tests verify the signature and edge case behavior of compute_auc according to specification."""
    # Test 1: Normal case
    y_true = np.array([1, 0, 0, 1])
    scores = np.array([0.8, 0.4, 0.6, 0.9])
    result = compute_auc(y_true, scores)
    assert isinstance(result, float), "Result must be a float"
    # Note: Exact value depends on implementation details of trapezoidal rule, but must be in [0,1]
    assert 0.0 <= result <= 1.0, "AUC must be in [0, 1]"

    # Test 2: No positive class present (d1=0) -> NaN
    y_true = np.array([False, False, False])
    scores = np.array([0.5, 0.6, 0.7])
    result = compute_auc(y_true, scores)
    assert np.isnan(result), "AUC must be NaN if no positive class"

    # Test 3: No negative class present (d2=0) -> NaN
    y_true = np.array([True, True, True])
    scores = np.array([0.1, 0.2, 0.3])
    result = compute_auc(y_true, scores)
    assert np.isnan(result), "AUC must be NaN if no negative class"

    # Test 4: Shape mismatch raises ValueError
    with pytest.raises(ValueError):
        compute_auc(np.array([1, 0]), np.array([1.0, 2.0, 3.0]))