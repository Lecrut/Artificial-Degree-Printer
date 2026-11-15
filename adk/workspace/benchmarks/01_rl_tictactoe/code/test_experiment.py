"""Tests for src/experiment module."""
import tempfile
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch
from src.config import get_default_config
from src.experiment import run_experiment

def test_run_experiment_produces_csv():
    """Verify that run_experiment produces a results CSV."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mock_config = MagicMock(spec=get_default_config().__class__)
        mock_config.seed = 42
        mock_config.num_runs = 1
        mock_config.max_steps = 3
        with patch('src.experiment.get_default_config', return_value=mock_config):
            with patch('src.experiment.write_csv'):
                with patch('src.experiment.plot_comparison_results'):
                    run_experiment()
    results_path = Path(tmpdir) / 'results.csv'
    assert results_path.exists(), 'Results CSV was not generated.'
    with open(results_path, 'r') as f:
        lines = f.readlines()
        assert len(lines) > 0, 'CSV file is empty.'
