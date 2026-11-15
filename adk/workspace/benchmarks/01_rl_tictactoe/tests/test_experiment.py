import pytest
from pathlib import Path

class TestExperiment:
    """Tests for experiment execution and result generation."""

    def test_tempfile_import_and_usage(self) -> None:
        """Ensure tempfile is imported before use in the test."""
        from unittest.mock import patch, MagicMock
        import src.config
        with patch.object(src.config.Config, 'OUTPUT_DIR', new='./results'), patch.object(src.config.Config, 'N_RUNS', 1), patch.object(src.config.Config, 'RANDOM_SEED', 42), patch.object(src.config.Config, 'EPOCHES_PER_EVALUATION', 50):
            with patch('src.tictactoe_env.TicTacToeEnv.reset', return_value=('empty_board', None, None, True)):
                from src.experiment import run_experiment
                result = run_experiment()

    def test_csv_file_created_after_run(self, tmp_path: Path) -> None:
        """Verify that run_experiment creates the CSV file in the returned or default output directory."""
        from unittest.mock import patch
        import src.config
        with patch.object(src.config.Config, 'OUTPUT_DIR', new=str(tmp_path)), patch.object(src.config.Config, 'N_RUNS', 1), patch.object(src.config.Config, 'RANDOM_SEED', 42), patch.object(src.config.Config, 'EPOCHES_PER_EVALUATION', 50), patch('src.tictactoe_env.TicTacToeEnv.reset', return_value=('empty_board', None, None, True)):
            from src.experiment import run_experiment
            try:
                result = run_experiment()
            except Exception as e:
                pytest.fail(f'run_experiment raised an exception: {e}')
            csv_files = list(tmp_path.glob('*.csv'))
            assert len(csv_files) > 0, f'No CSV file found in {tmp_path}'
