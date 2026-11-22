import numpy as np
from evaluation import compute_metrics, aggregate_metrics

def test_compute_metrics_signature():
    """Test that compute_metrics accepts the declared arguments."""
    import numpy as np
    from evaluation import compute_metrics
    y_true = np.array([0, 1, 0, 1])
    y_pred = np.array([0, 0, 0, 1])
    result_no_scores = compute_metrics(y_true=y_true, y_pred=y_pred, scores=None)
    assert isinstance(result_no_scores, dict)
    assert 'AUC_ROC' in result_no_scores
    assert 'PRECISION' in result_no_scores
    scores = np.array([0.5, 0.1, 0.9, 0.3])
    result_with_scores = compute_metrics(y_true=y_true, y_pred=y_pred, scores=scores)
    assert isinstance(result_with_scores, dict)
    assert 'AUC_ROC' in result_with_scores
    assert 'PRECISION' in result_with_scores

def test_compute_metrics_with_scores():
    """Test compute_metrics when 'scores' are provided."""
    y_true = np.array([0, 1, 0, 1])
    y_pred = np.array([0.2, 0.5, 0.8, 0.9])
    scores = np.array([0.1, 0.4, 0.7, 0.9])
    result = compute_metrics(y_true=y_true, y_pred=y_pred, scores=scores)
    assert isinstance(result, dict)
    assert 'AUC_ROC' in result

def test_aggregate_metrics_signature():
    """Test that aggregate_metrics accepts the declared argument."""
    import numpy as np
    from evaluation import aggregate_metrics
    per_run_results = [{'AUC_ROC': 0.9, 'F1_SCORE': 0.8, 'PRECISION': 0.75, 'RECALL': 0.85, 'SPECIFICITY': 0.7}, {'AUC_ROC': 0.95, 'F1_SCORE': 0.82, 'PRECISION': 0.8, 'RECALL': 0.88, 'SPECIFICITY': 0.75}]
    result = aggregate_metrics(per_run_results)
    assert isinstance(result, dict)
    assert 'AUC_ROC' in result
    assert 'PRECISION' in result
    assert 'F1_SCORE' in result
    assert 'RECALL' in result
    assert 'SPECIFICITY' in result
    assert 'AUC_ROC_STD' in result
    assert 'PRECISION_STD' in result
