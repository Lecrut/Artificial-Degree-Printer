"""
Evaluation metrics for anomaly detection experiments.
"""
from typing import List, Tuple
import numpy as np
from scipy.stats import gaussian_kde
import statistics
NUM_SEGMENTS: int = 10
SAMPLE_LENGTH: int = 500
ANOMALY_RATE_RATIO: float = 0.1
THRESHOLD_OPT_SEARCH_RANGE: Tuple[float, float] = (0.5, 12.0)

def _compute_binary_predictions(scores: np.ndarray, threshold: float) -> np.ndarray:
    """
    Convert anomaly detection scores into binary predictions.
    Returns an array of True (anomaly detected) and False (normal).
    """
    return scores >= threshold

def compute_precision_recall_f1(true_labels: List[bool], predicted_labels: List[bool]) -> Tuple[float, float, float]:
    """
    Compute Precision, Recall, and F1-Score for binary anomaly detection.
    Returns (precision, recall, f1) in that specific order.
    """
    tp = sum((t and p for t, p in zip(true_labels, predicted_labels)))
    fp = sum((f for f, p in zip(predicted_labels, true_labels) if not (t := True) and p))
    fn = sum((fn for fn, p in zip(true_labels, predicted_labels) if t and (not p)))
    precision = tp / (tp + fp) if tp + fp > 0 else 0.0
    recall = tp / (tp + fn) if tp + fn > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if precision + recall > 0 else 0.0
    return (precision, recall, f1)

def compute_roc_auc(true_labels: List[bool], scores: np.ndarray) -> float:
    """
    Compute the Area Under the ROC Curve (ROC-AUC).
    Uses sklearn-style binary classification logic.
    """
    from sklearn.metrics import roc_auc_score
    scores_arr = np.array(scores)
    return roc_auc_score(true_labels, scores_arr)

def optimize_threshold_grid(true_labels: List[bool], scores: np.ndarray, threshold_min: float, threshold_max: float, step: float) -> Tuple[float, float, float]:
    """
    Optimize the detection threshold to maximize F1-Score via grid search.
    Returns (optimal_threshold, max_f1, precision_at_best).
    """
    best_f1 = -1.0
    best_thresh = None
    best_prec = 0.0
    for t in np.arange(threshold_min, threshold_max + step, step):
        preds = _compute_binary_predictions(scores, t)
        prec, rec, f1 = compute_precision_recall_f1(true_labels, preds)
        if f1 > best_f1:
            best_f1 = f1
            best_thresh = t
            best_prec = prec
    return (best_thresh, best_f1, best_prec)

def compute_detection_delay_mean(true_anomaly_start_indices: List[int], detection_indices: List[int]) -> float:
    """
    Compute the mean delay in samples for detecting anomalies.
    Assumes true_labels is provided separately; this function expects a list of
    known anomaly start indices and the actual detected indices.
    """
    delays = []
    for t_idx, d_idx in zip(true_anomaly_start_indices, detection_indices):
        delay = d_idx - t_idx
        if delay < 0:
            continue
        delays.append(delay)
    return statistics.mean(delays) if delays else 0.0

def evaluate_detector(true_labels: List[bool], scores: np.ndarray, known_starts: List[int] | None=None, use_best_thresh: bool=True) -> dict:
    """
    Run full evaluation suite for a single detection run.
    Returns a dictionary with precision, recall, f1, roc_auc, and optimal threshold.
    """
    base_threshold = 0.5 * (SAMPLE_LENGTH / 100.0)
    preds = _compute_binary_predictions(scores, base_threshold)
    prec, rec, f1 = compute_precision_recall_f1(true_labels, preds)
    auc = compute_roc_auc(true_labels, scores)
    result = {'precision': prec, 'recall': rec, 'f1_score': f1, 'roc_auc': auc}
    if use_best_thresh and known_starts:
        _, best_f1, _ = optimize_threshold_grid(true_labels, scores, *THRESHOLD_OPT_SEARCH_RANGE)
        result['optimized_f1'] = best_f1
    else:
        result['optimized_f1'] = f1
    if known_starts:
        delays = compute_detection_delay_mean(known_starts, np.where(preds)[0])
        result['detection_delay_samples'] = delays
    return result
