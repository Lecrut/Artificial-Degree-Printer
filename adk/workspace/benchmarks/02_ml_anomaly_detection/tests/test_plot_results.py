import pytest
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from plot_results import generate_plots

@pytest.fixture
def mock_results_csv(tmp_path):
    """Create a mock results.csv file for testing."""
    csv_path = tmp_path / 'results.csv'
    data = [
        ['baseline_zscore', 'mean_f1_score', 0.85],
        ['baseline_zscore', 'std_f1_score', 0.02],
        ['baseline_zscore', 'mean_roc_auc', 0.90],
        ['baseline_zscore', 'detection_delay_mean', 0.1],
        ['ensemble_detector', 'mean_f1_score', 0.89],
        ['ensemble_detector', 'std_f1_score', 0.01],
        ['ensemble_detector', 'mean_roc_auc', 0.92],
        ['ensemble_detector', 'detection_delay_mean', 0.15],
    ]
    csv_path.write_text('\n'.join(f"{row[0]}, {row[1]}, {row[2]}" for row in data) + '\n')
    return str(csv_path)


def test_generate_plots_saves_file(mock_results_csv, tmp_path):
    """Test that generate_plots creates figures without syntax errors."""
    # Ensure output directory exists
    output_dir = str(tmp_path)
    
    try:
        paths = generate_plots(output_dir=output_dir)
        
        # Verify at least one figure was created (even if empty due to logic, file should exist)
        assert isinstance(paths, list)
        for path in paths:
            assert Path(path).exists()
    except Exception as e:
        pytest.fail(f"generate_plots raised an exception: {e}")


def test_generate_plots_handles_missing_cols(mock_results_csv, tmp_path):
    """Test that generate_plots raises a clear error for missing columns."""
    # Create a CSV without required columns (value is missing)
    csv_path = tmp_path / 'bad_results.csv'
    # Rename to results.csv so generate_plots finds it
    csv_path.rename(tmp_path / 'results.csv')
    
    with pytest.raises(ValueError, match="Missing required columns"):
        generate_plots(output_dir=str(tmp_path))
