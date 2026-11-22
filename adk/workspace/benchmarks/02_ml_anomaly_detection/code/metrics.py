"""Utility functions for evaluating anomaly detection performance."""
import numpy as np
from typing import Union

def calculate_auc_roc(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute the Area Under the Receiver Operating Characteristic curve (AUC-ROC).

    Args:
        y_true: Binary ground truth labels. Shape: (n_samples,). Expected values are 0 or 1.
        y_pred: Predicted scores or probabilities for the positive class. Shape: (n_samples,).
                Should be continuous values in range [0, 1] or unbounded scores;
                the function computes ROC over multiple thresholds internally.

    Returns:
        float: AUC-ROC score in range [0.0, 1.0].
               0.5 indicates random guessing; 1.0 indicates perfect separation.

    Raises:
        ValueError: If inputs have different shapes or lengths.
    """
    from sklearn.metrics import roc_auc_score
    if len(y_true) != len(y_pred):
        raise ValueError('Input arrays must have the same length.')
    y_true_arr = np.asarray(y_true)
    y_pred_arr = np.asarray(y_pred)
    if y_true_arr.shape[0] != len(y_pred_arr):
        raise ValueError('Input arrays must have the same length.')
    try:
        auc_score = roc_auc_score(y_true_arr, y_pred_arr, average=None)
    except (ValueError, RuntimeWarning) as e:
        if 'all positive' in str(e).lower() or 'no class' in str(e).lower():
            raise ValueError('Input data must contain both positive and negative classes.') from e
        raise
    return float(auc_score)

def calculate_f1_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute the F1-score (harmonic mean of precision and recall).

    Args:
        y_true: Binary ground truth labels. Shape: (n_samples,). Expected values are 0 or 1.
        y_pred: Predicted binary labels (thresholded predictions). Shape: (n_samples,).
                Expected values are 0 or 1.

    Returns:
        float: F1 score in range [0.0, 1.0].
               0.0 indicates no true positives; 1.0 indicates perfect precision and recall.

    Edge Cases:
        - If both precision and recall are 0 (no predicted positives and/or no true positives),
          returns 0.0 by convention.
        - If inputs are empty, returns 0.0.
    """
    from sklearn.metrics import f1_score
    if len(y_true) != len(y_pred):
        raise ValueError('Input arrays must have the same length.')
    y_true_arr = np.asarray(y_true)
    y_pred_arr = np.asarray(y_pred)
    if y_true_arr.shape[0] != len(y_pred_arr):
        raise ValueError('Input arrays must have the same length.')
    try:
        f1 = f1_score(y_true_arr, y_pred_arr, pos_label=1)
    except (ValueError, RuntimeWarning) as e:
        if 'all positive' in str(e).lower() or 'no class' in str(e).lower():
            raise ValueError('Input data must contain both positive and negative classes.') from e
        raise
    return float(f1)
