import pytest
import csv
import os
from pathlib import Path

def test_results_csv_integrity():
    '''Verify results.csv has correct schema and valid numerical data.'''
    # Assume current directory for test context
    csv_path = Path("results.csv")
    assert csv_path.exists(), "results.csv must exist"
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Check schema columns
    expected_cols = {'method', 'rounds', 'final_accuracy', 'latency_ms'}
    assert set(rows[0].keys()) == expected_cols, f"Columns mismatch: {rows[0].keys()}"
    
    # Check rows
    methods = [r['method'] for r in rows]
    assert 'baseline' in methods, "Missing baseline row"
    assert 'proposed' in methods, "Missing proposed row"
    
    # Check data types and range validity
    for row in rows:
        # Rounds should be int
        assert int(row['rounds']) > 0
        
        # Accuracy should be between 0 and 1
        acc = float(row['final_accuracy'])
        assert 0.0 <= acc <= 1.0, f"Invalid accuracy {acc}"
        
        # Latency should be positive
        lat = float(row['latency_ms'])
        assert lat > 0, f"Invalid latency {lat}"

def test_proposed_superiority():
    '''Verify proposed method has higher accuracy than baseline in results.csv.'''
    csv_path = Path("results.csv")
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = {r['method']: float(r['final_accuracy']) for r in reader}
    
    assert rows['proposed'] > rows['baseline'], "Proposed method should have higher accuracy than baseline"
