import pytest
import csv
from pathlib import Path

def test_results_csv_structure():
    '''Verify results.csv has correct columns and rows.'''
    csv_path = Path("results.csv")
    assert csv_path.exists(), "results.csv must exist"
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        expected = ['method', 'rounds', 'avg_expanded_nodes', 'path_optimality', 'speedup_factor', 'success_rate']
        assert headers == expected, f"Headers mismatch: {headers} != {expected}"
        
        rows = list(reader)
        methods = [row['method'] for row in rows]
        assert 'baseline' in methods, "Baseline row missing"
        assert 'proposed' in methods, "Proposed row missing"

def test_performance_metrics_validity():
    '''Verify proposed method is faster (higher speedup) and expands fewer nodes.'''
    csv_path = Path("results.csv")
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        data = {row['method']: row for row in reader}
        
        baseline_nodes = float(data['baseline']['avg_expanded_nodes'])
        proposed_nodes = float(data['proposed']['avg_expanded_nodes'])
        speedup = float(data['proposed']['speedup_factor'])
        
        # A* should expand fewer nodes than Dijkstra on typical grids
        assert proposed_nodes < baseline_nodes, f"A* should expand fewer nodes: {proposed_nodes} vs {baseline_nodes}"
        # Speedup factor should be > 1.0 (assuming defined as baseline/proposed time) or similar metric
        # In the input CSV, speedup_factor for proposed is 2.35, implying it is faster.
        assert speedup > 1.0, "Speedup factor must be greater than 1"
