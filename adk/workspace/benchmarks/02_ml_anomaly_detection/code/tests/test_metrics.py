import pytest
import numpy as np
from metrics import calculate_auc_roc, calculate_f1_score

def test_calculate_auc_roc_perfect_separation():
    """Test AUC-ROC for perfectly separated classes (AUC=1)."""
    y_true = [0, 0, 0, 1, 1, 1]
    # Scores strictly separate negatives (low) from positives (high)
    y_pred = [0.1, 0.2, 0.3, 0.7, 0.8, 0.9]
    auc_value = calculate_auc_roc(y_true, y_pred)
    assert isinstance(auc_value, (int, float))
    assert abs(auc_value - 1.0) < 1e-6

def test_calculate_auc_roc_random():
    """Test AUC-ROC for random predictions (AUC ~ 0.5)."""
    rng = np.random.RandomState(42)
    y_true = [0, 1] * 100
    y_pred = list(rng.rand(200))
    auc_value = calculate_auc_roc(y_true, y_pred)
    assert isinstance(auc_value, (int, float))
    # For random data, AUC should be roughly 0.5. Allow a wider margin.
    assert 0.4 < auc_value < 0.6

def test_calculate_auc_roc_empty_inputs():
    """Test AUC-ROC with empty inputs returns a valid scalar."""
    y_true = []
    y_pred = []
    # Depending on implementation, this might raise or return 0/None.
    # Spec says "handles edge cases gracefully", usually implies returning
    # a numeric type or raising specific error. Assuming graceful return
    # of a scalar for empty set is common in custom impls to avoid crashes,
    # but mathematically undefined. We check it returns a scalar as per
    # existing basic tests pattern which asserts isinstance(auc_value, (int, float))
    auc_value = calculate_auc_roc(y_true, y_pred)
    assert isinstance(auc_value, (int, float))

def test_calculate_f1_score_perfect():
    """Test F1 score for perfect predictions (F1=1)."""
    y_true = [0, 0, 1, 1]
    y_pred = [0, 0, 1, 1]
    f1_value = calculate_f1_score(y_true, y_pred)
    assert isinstance(f1_value, (int, float))
    assert abs(f1_value - 1.0) < 1e-6

def test_calculate_f1_score_zero_true_positives():
    """Test F1 score when there are no true positives (F1=0)."""
    y_true = [0, 0, 0]
    y_pred = [0, 0, 0]
    f1_value = calculate_f1_score(y_true, y_pred)
    assert isinstance(f1_value, (int, float))
    assert abs(f1_value - 0.0) < 1e-6

def test_calculate_f1_score_basic_errors():
    """Test F1 score with some mismatches."""
    y_true = [0, 0, 1, 1]
    y_pred = [0, 1, 1, 1]
    # TP=2, FP=1, FN=1
    # Precision = 2/3, Recall = 2/2 = 1
    # F1 = 2 * (2/3 * 1) / (2/3 + 1) = (4/3) / (5/3) = 0.8
    f1_value = calculate_f1_score(y_true, y_pred)
    assert isinstance(f1_value, (int, float))
    assert abs(f1_value - 0.8) < 1e-6