from evaluation import compute_metrics, aggregate_results
import numpy as np

def test_compute_metrics():
    """Test compute_metrics behavior and return values."""
    y_true = np.array([0, 0, 1, 1])
    y_scores = np.array([0.1, 0.9, 0.8, 0.2])
    threshold = 0.5
    metrics = compute_metrics(y_true, y_scores, threshold)
    assert 'precision' in metrics
    assert 'recall' in metrics
    assert 'f1' in metrics
    assert 'roc_auc' in metrics
    assert isinstance(metrics['precision'], float)
    assert isinstance(metrics['recall'], float)
    assert isinstance(metrics['f1'], float)
    assert isinstance(metrics['roc_auc'], float)
    assert abs(metrics['precision'] - 0.5) < 0.0001
    assert abs(metrics['recall'] - 0.5) < 0.0001
    assert abs(metrics['f1'] - 0.5) < 0.0001
    assert abs(metrics['roc_auc'] - 0.5) < 0.0001

def test_compute_metrics_with_threshold():
    """Test that threshold is used correctly for binarization."""
    y_true = np.array([0, 1, 0, 1])
    y_scores = np.array([0.2, 0.9, 0.8, 0.1])
    metrics_low = compute_metrics(y_true, y_scores, 0.3)
    metrics_high = compute_metrics(y_true, y_scores, 0.8)
    assert abs(metrics_low['precision'] - 0.5) < 0.0001
    assert abs(metrics_high['precision'] - 0.5) < 0.0001

def test_aggregate_results():
    """Test aggregate_results behavior and aggregation logic."""
    runs = [{'m1': {'acc': 0.9}, 'm2': {'acc': 0.8}}, {'m1': {'acc': 0.95}, 'm2': {'acc': 0.85}}]
    res = aggregate_results(runs)
    assert isinstance(res, list)
    for r in res:
        assert 'method' in r
        assert 'metric' in r
        assert 'value' in r
        assert 'std_dev' in r
    m1_acc_row = [r for r in res if r['method'] == 'm1' and r['metric'] == 'acc'][0]
    expected_m1_acc = 0.925
    assert abs(m1_acc_row['value'] - expected_m1_acc) < 0.0001, f"Expected mean {expected_m1_acc}, got {m1_acc_row['value']}"
    expected_std = np.std([0.9, 0.95], ddof=1)
    assert abs(m1_acc_row['std_dev'] - expected_std) < 1e-06
if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
