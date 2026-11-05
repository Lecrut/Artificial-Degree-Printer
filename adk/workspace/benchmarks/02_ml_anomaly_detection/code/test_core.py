import unittest
import csv
import os
from pathlib import Path

class TestBioSignalBenchmark(unittest.TestCase):
    def test_results_csv_integrity(self):
        """Verify results.csv exists, has correct schema, and matches expected values from payload."""
        csv_path = Path("results.csv")
        self.assertTrue(csv_path.exists(), "results.csv must exist")
        
        with open(csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Check columns
            expected_cols = {'method', 'precision', 'recall', 'f1_score', 'false_alarm_rate'}
            self.assertEqual(set(reader.fieldnames), expected_cols)
            
            # Check row count and methods
            methods = {row['method'] for row in rows}
            self.assertIn('baseline', methods)
            self.assertIn('proposed', methods)
            
            # Check specific values from payload
            data = {row['method']: row for row in rows}
            baseline_f1 = float(data['baseline']['f1_score'])
            proposed_f1 = float(data['proposed']['f1_score'])
            
            self.assertAlmostEqual(baseline_f1, 0.6860, places=4)
            self.assertAlmostEqual(proposed_f1, 0.9034, places=4)
            
            # Verify Proposed is better
            self.assertGreater(proposed_f1, baseline_f1)

class TestConfigImports(unittest.TestCase):
    def test_config_constants(self):
        """Verify config.py has required constants with correct types/values."""
        try:
            import config
        except ImportError:
            self.skipTest("config.py not available")
            
        self.assertTrue(hasattr(config, 'N_SAMPLES'))
        self.assertEqual(config.N_SAMPLES, 600)
        
        self.assertTrue(hasattr(config, 'ANOMALY_RATIO'))
        self.assertEqual(config.ANOMALY_RATIO, 0.08)
        
        self.assertTrue(hasattr(config, 'Z_THRESHOLD'))
        self.assertAlmostEqual(config.Z_THRESHOLD, 2.4, places=1)
        
        self.assertTrue(hasattr(config, 'ENSEMBLE_TREES'))
        self.assertEqual(config.ENSEMBLE_TREES, 25)

if __name__ == '__main__':
    unittest.main()