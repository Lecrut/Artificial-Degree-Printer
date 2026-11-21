"""Computes classification metrics and aggregates statistical summaries for repeated experiments."""
from typing import List, Dict
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
N_RUNS: int = 10

def compute_metrics(y_true: np.ndarray, y_scores: np.ndarray, threshold: float=0.5) -> Dict[str, float]:
    """Computes precision, recall, f1 from thresholded scores and roc_auc from raw scores.

    The threshold is used to convert continuous anomaly scores into binary predictions 
    for precision, recall, and f1-score calculation.
    """
    y_pred = (y_scores >= threshold).astype(int)
    if y_true.ndim == 2:
        y_true = y_true.flatten()
    if y_pred.ndim == 2:
        y_pred = y_pred.flatten()
    tp_count = int(np.sum((y_pred == 1) & (y_true == 1)))
    fp_count = int(np.sum((y_pred == 1) & (y_true == 0)))
    fn_count = int(np.sum((y_pred == 0) & (y_true == 1)))
    if tp_count + fp_count == 0:
        precision = 0.0
    else:
        precision = tp_count / (tp_count + fp_count)
    if tp_count + fn_count == 0:
        recall = 0.0
    else:
        recall = tp_count / (tp_count + fn_count)
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * (precision * recall) / (precision + recall)
    try:
        roc_auc = float(roc_auc_score(y_true, y_scores))
    except ValueError:
        roc_auc = 0.5
    return {'precision': precision, 'recall': recall, 'f1': f1, 'roc_auc': roc_auc}

def aggregate_results(runs_data: List[Dict[str, Dict[str, float]]]) -> List[Dict[str, float | str]]:
    """Aggregates results from multiple experimental runs into summary rows for CSV output.

    Calculates mean and standard deviation for each metric across the provided runs.
    The result is a list of dictionaries, one per unique method and metric combination,
    containing 'method', 'metric', 'value' (mean) and 'std_dev' (standard deviation).
    """
    metrics_list = []
    seen_keys = set()
    for run in runs_data:
        for method_name, metrics in run.items():
            for metric_name, metric_value in metrics.items():
                key = f'{method_name}_{metric_name}'
                if key not in seen_keys:
                    seen_keys.add(key)
                    new_item = {'key': key, 'method': method_name, 'metric': metric_name, 'values': [v for v in (run.get(method_name, {}).get(metric_name, np.nan) for run in runs_data if metric_name in run.get(method_name, {})) if not np.isnan(v)]}
                    vals = []
                    for r in runs_data:
                        m = r.get(method_name, {})
                        if metric_name in m:
                            v = m[metric_name]
                            if not np.isnan(v):
                                vals.append(v)
                    new_item['values'] = vals
                    metrics_list.append(new_item)
    final_results = []
    for item in metrics_list:
        values = item['values']
        method_name = item['method']
        metric_name = item['metric']
        if len(values) > 0:
            mean_val = float(np.mean(values))
            std_dev = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
            final_results.append({'method': method_name, 'metric': metric_name, 'value': mean_val, 'std_dev': std_dev})
    return final_results
