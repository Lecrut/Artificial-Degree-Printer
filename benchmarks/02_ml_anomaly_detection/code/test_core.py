import csv
from pathlib import Path

def test_results_csv_structure():
    """Verify results.csv has required columns for baseline and proposed methods."""
    csv_path = Path('results.csv')
    assert csv_path.exists(), "results.csv must exist"
    
    with open(csv_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        required_cols = ['method', 'baseline_precision', 'baseline_recall', 'baseline_f1_score', 'baseline_false_alarm_rate', 'proposed_precision', 'proposed_recall', 'proposed_f1_score', 'proposed_false_alarm_rate']
        for col in required_cols:
            assert col in headers, f"Missing column: {col}"

        rows = list(reader)
        assert len(rows) >= 1, "Must have at least one data row"
        
        # Verify method names
        methods = [row['method'] for row in rows]
        assert 'baseline' in methods
        assert 'proposed' in methods