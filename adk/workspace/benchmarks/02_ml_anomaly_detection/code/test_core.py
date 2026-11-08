from __future__ import annotations

import csv
import os
import sys
from typing import Any

# Inject sys.path for local module imports BEFORE any other imports
current_dir: str = os.path.dirname(os.path.abspath(__file__))
parent_dir: str = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import numpy as np
import pytest

# Import config to verify constants
from config import ANOMALY_RATIO  # noqa: F401
from config import ENSEMBLE_TREES  # noqa: F401
from config import N_SAMPLES  # noqa: F401
from config import Z_THRESHOLD  # noqa: F401

# Test Config Constants
@pytest.fixture
def valid_config() -> dict[str, float]:
    return {
        'N_SAMPLES': 600,
        'ANOMALY_RATIO': 0.08,
        'Z_THRESHOLD': 2.4,
        'ENSEMBLE_TREES': 25
    }

def test_config_constants(valid_config: dict[str, float]) -> None:
    assert N_SAMPLES == valid_config['N_SAMPLES'], "N_SAMPLES mismatch"
    assert ANOMALY_RATIO == valid_config['ANOMALY_RATIO'], "ANOMALY_RATIO mismatch"
    assert Z_THRESHOLD == valid_config['Z_THRESHOLD'], "Z_THRESHOLD mismatch"
    assert ENSEMBLE_TREES == valid_config['ENSEMBLE_TREES'], "ENSEMBLE_TREES mismatch"

def test_core_imports() -> None:
    try:
        from core import generate_biosignal_dataset  # noqa: F401
        from core import train_and_evaluate  # noqa: F401
        assert callable(generate_biosignal_dataset)
        assert callable(train_and_evaluate)
    except ImportError as e:
        pytest.fail(f"Failed to import core modules: {e}")

# Test Biosignal Generation
def test_biosignal_generation() -> None:
    from core import generate_biosignal_dataset
    
    # Test with small n_samples for speed
    signals, labels = generate_biosignal_dataset(n_samples=100, anomaly_ratio=0.1, seed=42)
    
    # Check shapes
    assert len(signals) == 100, f"Expected 100 samples, got {len(signals)}"
    assert len(labels) == 100, f"Expected 100 labels, got {len(labels)}"
    
    # Check types
    assert isinstance(signals, np.ndarray), "Signals should be numpy array"
    assert isinstance(labels, np.ndarray), "Labels should be numpy array"
    
    # Check anomaly count: int(100 * 0.1) = 10
    expected_anomalies: int = 10
    actual_anomalies: int = sum(labels)
    assert actual_anomalies == expected_anomalies, f"Expected {expected_anomalies} anomalies, got {actual_anomalies}"
    
    # Check labels are binary
    unique_labels: set[int] = set(labels.tolist())
    assert unique_labels.issubset({0, 1}), "Labels must be binary (0 or 1)"

# Test Comparative Evaluation Logic
@pytest.fixture
def temp_csv(tmp_path: Any) -> str:
    return str(tmp_path / "test_results.csv")

def test_evaluate_comparative(temp_csv: str) -> None:
    from core import train_and_evaluate
    
    # Run evaluation
    results: dict[str, dict[str, float]] = train_and_evaluate(temp_csv, seed=42)
    
    # Check returned dictionary structure
    assert 'baseline' in results, "Missing 'baseline' in results"
    assert 'proposed' in results, "Missing 'proposed' in results"
    
    # Check metrics keys
    required_metrics: list[str] = ['precision', 'recall', 'f1_score', 'false_alarm_rate']
    for model in ['baseline', 'proposed']:
        for metric in required_metrics:
            assert metric in results[model], f"Missing metric {metric} for {model}"
            assert isinstance(results[model][metric], float), f"Metric {metric} should be float for {model}"
    
    # Check CSV file creation
    assert os.path.exists(temp_csv), "CSV file was not created"
    
    # Verify CSV content structure
    with open(temp_csv, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        # Check column names (updated to match new schema)
        expected_cols: list[str] = ['method', 'precision', 'recall', 'f1_score', 'false_alarm_rate']
        assert set(rows[0].keys()) == set(expected_cols), f"CSV columns mismatch: {rows[0].keys()} vs {expected_cols}"
        
        # Check row count
        assert len(rows) == 2, f"Expected 2 rows in CSV, got {len(rows)}"
        
        # Check methods present
        methods: list[str] = [row['method'] for row in rows]
        assert 'baseline' in methods, "Missing 'baseline' row in CSV"
        assert 'proposed' in methods, "Missing 'proposed' row in CSV"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])