import csv
import os
import pytest

def test_results_csv_schema():
    '''Verify that results.csv exists and contains the exact columns required by the thesis.'''
    if not os.path.exists('results.csv'):
        pytest.skip("results.csv does not exist; run benchmarks first.")
    
    with open('results.csv', 'r', newline='') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        rows = list(reader)
    
    # Check required columns based on input schema and task description
    expected_cols = ['method', 'rounds', 'avg_expanded_nodes', 'path_optimality', 'speedup_factor', 'success_rate']
    for col in expected_cols:
        assert col in headers, f"Missing column: {col}. Found: {headers}"
    
    # Check row selectors
    methods = [row['method'] for row in rows]
    assert 'baseline' in methods, "Missing 'baseline' row in results.csv"
    assert 'proposed' in methods, "Missing 'proposed' row in results.csv"

def test_results_data_integrity():
    '''Verify that numeric columns contain valid float values.'''
    if not os.path.exists('results.csv'):
        pytest.skip("results.csv does not exist.")
    
    with open('results.csv', 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                float(row['avg_expanded_nodes'])
                float(row['path_optimality'])
                float(row['speedup_factor'])
                float(row['success_rate'])
            except ValueError:
                pytest.fail(f"Non-numeric value in row: {row}")