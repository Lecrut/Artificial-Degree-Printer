import csv
import math
import random
from pathlib import Path
import config


def generate_biosignal_dataset(
    n_samples: int = config.N_SAMPLES,
    anomaly_ratio: float = config.ANOMALY_RATIO,
    seed: int = 42,
) -> tuple[list[tuple[float, float, float]], list[int]]:
    """Generate 3-channel synthetic physiological telemetry (HR, HRV-RMSSD, SpO2-drop) with binary anomaly labels."""
    rng = random.Random(seed)
    n_anomalies = max(1, int(round(n_samples * anomaly_ratio)))
    anomaly_indices = set(rng.sample(range(n_samples), n_anomalies))

    features: list[tuple[float, float, float]] = []
    labels: list[int] = []

    for idx in range(n_samples):
        phase = 2.0 * math.pi * (idx / 60.0)
        if idx in anomaly_indices:
            # Multi-channel correlated cardiac/respiratory anomaly spike
            hr = 72.0 + 6.0 * math.sin(phase) + rng.gauss(22.0, 4.5)
            hrv = 45.0 - rng.gauss(19.0, 3.5)
            spo2_drop = abs(rng.gauss(4.8, 0.9))
            labels.append(1)
        else:
            hr = 72.0 + 6.0 * math.sin(phase) + rng.gauss(0.0, 3.2)
            hrv = 45.0 + 3.0 * math.cos(phase) + rng.gauss(0.0, 2.8)
            spo2_drop = max(0.0, rng.gauss(0.6, 0.35))
            labels.append(0)
        features.append((hr, hrv, spo2_drop))

    return features, labels


def _compute_classification_metrics(y_true: list[int], y_pred: list[int]) -> dict[str, float]:
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2.0 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    far = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1_score": round(f1, 3),
        "false_alarm_rate": round(far, 4),
    }


def train_and_evaluate(csv_out_path: str | Path | None = None, seed: int = 42) -> dict[str, float]:
    features, labels = generate_biosignal_dataset(
        n_samples=config.N_SAMPLES,
        anomaly_ratio=config.ANOMALY_RATIO,
        seed=seed,
    )

    # 1. Baseline: Univariate Z-Score on channel 0 (Heart Rate only)
    hrs = [row[0] for row in features]
    mean_hr = sum(hrs) / len(hrs)
    std_hr = math.sqrt(sum((x - mean_hr) ** 2 for x in hrs) / len(hrs)) or 1.0
    baseline_preds = [1 if abs(x - mean_hr) / std_hr > config.Z_THRESHOLD else 0 for x in hrs]
    base_m = _compute_classification_metrics(labels, baseline_preds)

    # 2. Proposed: Robust Median/MAD Multi-Channel Ensemble with subspace projections
    rng = random.Random(seed + 7)
    n_dims = 3
    medians = []
    mads = []
    for d in range(n_dims):
        col = sorted(row[d] for row in features)
        med = col[len(col) // 2]
        abs_dev = sorted(abs(x - med) for x in col)
        mad = (abs_dev[len(abs_dev) // 2] * 1.4826) or 1e-6
        medians.append(med)
        mads.append(mad)

    # Ensemble of random subspace hyperplanes + robust radial distance
    ensemble_votes = [0.0] * len(features)
    for _ in range(config.ENSEMBLE_TREES):
        weights = [rng.uniform(0.5, 1.5) for _ in range(n_dims)]
        w_norm = math.sqrt(sum(w * w for w in weights))
        weights = [w / w_norm for w in weights]
        for idx, row in enumerate(features):
            z_vec = [(row[d] - medians[d]) / mads[d] for d in range(n_dims)]
            radial = math.sqrt(sum(weights[d] * (z_vec[d] ** 2) for d in range(n_dims)))
            if radial > config.Z_THRESHOLD:
                ensemble_votes[idx] += 1.0

    proposed_preds = [1 if (vote / config.ENSEMBLE_TREES) >= 0.5 else 0 for vote in ensemble_votes]
    prop_m = _compute_classification_metrics(labels, proposed_preds)

    baseline_row = {
        "method": "baseline",
        "samples": float(config.N_SAMPLES),
        **base_m,
    }
    proposed_row = {
        "method": "proposed",
        "samples": float(config.N_SAMPLES),
        **prop_m,
    }

    if csv_out_path is not None:
        out_p = Path(csv_out_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with out_p.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["method", "samples", "precision", "recall", "f1_score", "false_alarm_rate"],
            )
            writer.writeheader()
            writer.writerow(baseline_row)
            writer.writerow(proposed_row)

    return proposed_row
