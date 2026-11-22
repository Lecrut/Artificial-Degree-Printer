"""Module for computing classification metrics and aggregating results for anomaly detection evaluation."""
from sklearn.metrics import auc, precision_score, recall_score
from typing import Dict, List
import numpy as np
import sklearn.metrics

def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, scores: np.ndarray | None=None) -> dict:
    """
    Compute AUC_ROC, F1_SCORE, PRECISION, RECALL, and SPECIFICITY for binary anomaly detection.

    Takes ground truth labels `y_true` (0=normal, 1=anomaly), predicted binary labels `y_pred`,
    and optional continuous anomaly `scores`. Returns a dictionary with computed metrics.
    """
    n_positives = np.sum(y_true)
    n_negatives = len(y_true) - n_positives
    if n_positives == 0 or n_negatives == 0:
        return {'AUC_ROC': 0.5, 'F1_SCORE': 0.5, 'PRECISION': 0.5, 'RECALL': 0.5, 'SPECIFICITY': 0.5}
    if scores is None:
        auc_roc = 0.5
        precision = np.nan
        recall = np.nan
        specificity = np.nan
    else:
        auc_roc = 0
        sorted_indices = np.argsort(scores)
        pos_labels = y_true[sorted_indices]
        neg_labels = (1 - y_true)[sorted_indices]
        if len(pos_labels) == 0 or len(neg_labels) == 0:
            auc_roc = 0.5
        else:
            total_pos = len(pos_labels)
            total_neg = len(neg_labels)
            rank_sum_positive = np.sum(np.where(y_true == 1, np.arange(len(scores)) + 1, 0))
            if total_pos > 0 and total_neg > 0:
                auc_roc = (rank_sum_positive - total_pos * (total_pos + 1) / 2) / (total_pos * total_neg)
                auc_roc = max(0.0, min(1.0, auc_roc))
            else:
                auc_roc = 0.5
        std_scores = np.std(scores)
        if std_scores == 0 or len(set(np.unique(scores))) < 2:
            auc_roc = 0.5
        else:
            pass
    tp = np.sum((y_pred == 1) & (y_true == 1))
    fp = np.sum((y_pred == 1) & (y_true == 0))
    fn = np.sum((y_pred == 0) & (y_true == 1))
    tn = np.sum((y_pred == 0) & (y_true == 0))
    precision = tp / (tp + fp) if tp + fp > 0 else 0.0
    recall = tp / (tp + fn) if tp + fn > 0 else 0.0
    specificity = tn / (tn + fp) if tn + fp > 0 else 0.0
    f1_score = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0.0
    auc_roc = float(auc_roc)
    result = {'AUC_ROC': auc_roc, 'F1_SCORE': float(f1_score), 'PRECISION': precision, 'RECALL': recall, 'SPECIFICITY': specificity}
    return result

def aggregate_metrics(per_run_results: list[dict]) -> dict:
    """
    Aggregate metrics from multiple independent runs into final statistics.

    Takes a list of dictionaries containing metric results. Returns mean values with std devs.
    """
    if not per_run_results:
        return {'AUC_ROC': 0.0, 'F1_SCORE': 0.0, 'PRECISION': 0.0, 'RECALL': 0.0, 'SPECIFICITY': 0.0, 'AUC_ROC_STD': 0.0, 'F1_SCORE_STD': 0.0, 'PRECISION_STD': 0.0, 'RECALL_STD': 0.0, 'SPECIFICITY_STD': 0.0}
    means = {key: np.mean([r[key] for r in per_run_results]) for key in ['AUC_ROC', 'F1_SCORE', 'PRECISION', 'RECALL', 'SPECIFICITY']}
    stds = {f'{key}_STD': float(np.std([r[key] for r in per_run_results])) for key in ['AUC_ROC', 'F1_SCORE', 'PRECISION', 'RECALL', 'SPECIFICITY']}
    return {**means, **stds}
