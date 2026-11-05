import csv
from pathlib import Path

def test_results_csv_structure():
    '''Verify results.csv has correct columns and row selectors.'''
    p = Path('results.csv')
    assert p.exists(), "results.csv does not exist"
    
    with open(p, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    expected_cols = ['method', 'rounds', 'final_accuracy', 'latency_ms', 'straggler_resilience_rate']
    assert set(expected_cols) == set(rows[0].keys()), f"Columns mismatch: {rows[0].keys()}"
    
    methods = [r['method'] for r in rows]
    assert 'baseline' in methods, "Missing 'baseline' row"
    assert 'proposed' in methods, "Missing 'proposed' row"

def test_results_data_integrity():
    '''Verify data types and plausible ranges.'''
    p = Path('results.csv')
    with open(p, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    for row in rows:
        assert float(row['rounds']) > 0
        assert 0.0 <= float(row['final_accuracy']) <= 1.0
        assert float(row['latency_ms']) > 0
        assert 0.0 <= float(row['straggler_resilience_rate']) <= 1.0
