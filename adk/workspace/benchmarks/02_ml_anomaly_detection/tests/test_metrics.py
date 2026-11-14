import sys
sys.path.insert(0, 'src')
import numpy as np
from evaluation.metrics import compute_precision_recall_f1, compute_roc_auc, compute_detection_delay_mean, evaluate_detector

class TestMetricCalculations:

    def test_compute_precision_recall_f1(self):
        """Test F1 calculation against ground truth."""
        true_labels = [True, True, False, False, False]
        pred_labels = [False, True, False, True, True]
        f1_val = compute_precision_recall_f1(true_labels, pred_labels)[2]
        assert not np.isnan(f1_val), 'F1 score must be finite'
        assert abs(f1_val - 2.0 / 3.0) < 1e-06, f'Expected F1=0.667, got {f1_val}'

    def test_compute_roc_auc(self):
        """Test ROC-AUC calculation."""
        true_labels = [1, 1, 1, 1]
        scores = [0.9, 0.8, 0.2, 0.1]
        result = compute_roc_auc(true_labels, np.array(scores))
        assert not np.isnan(result), 'AUC must be finite'
        assert abs(result - 1.0) < 1e-06, f'Expected AUC=1.0, got {result}'

    def test_compute_detection_delay_mean(self):
        """Test detection delay calculation."""
        true_times = np.array([10, 20])
        pred_times = np.array([12, 18])
        result = compute_detection_delay_mean(true_times, pred_times)
        expected_delay = (2 + 2) / 2.0
        assert not np.isnan(result), 'Delay must be finite'
        assert abs(result - expected_delay) < 1e-06, f'Expected delay={expected_delay}, got {result}'

    def test_evaluate_detector_integration(self):
        """Test full evaluation pipeline with mocked data."""
        true_labels = [False, False, True]
        scores = np.array([0.5, 0.3, 0.9])
        known_starts = [2]
        result_dict = evaluate_detector(true_labels, scores, known_starts=known_starts)
        f1_val = result_dict['f1_score']
        roc_auc = result_dict['roc_auc']
        delay_mean = result_dict['delay_mean']
        assert not np.isnan(f1_val), 'Integration: F1 must be finite'
        assert not np.isnan(roc_auc), 'Integration: ROC-AUC must be finite'
        assert not np.isnan(delay_mean), 'Integration: Delay must be finite'
