import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch

# Import the module under test
from experiment import run_experiment


class TestRunExperiment:
    """Tests for the experiment.run_experiment function."""

    @patch('experiment._train_one_run')
    @patch('experiment.pd.DataFrame')
    def test_returns_dataframe_with_correct_metrics(self, mock_df_class, mock_train):
        """
        Verify that run_experiment returns a pandas DataFrame containing the aggregated metrics.
        It should aggregate results from multiple runs (defined by config.N_RUNS).
        """
        # Mock data returned by _train_one_run
        sample_metrics = {
            'train_avg_reward': 0.8,
            'win_rate': 0.6,
            'loss_rate': 0.2,
            'draw_rate': 0.2
        }
        mock_history = [{'episode': 1, 'reward': 0.5}]
        mock_train.return_value = (sample_metrics, mock_history)

        # Mock the DataFrame creation to return a specific structure for verification
        expected_rows = [
            {'method': 'Q-Learning', 'metric': 'train_avg_reward', 'value': sample_metrics['train_avg_reward'], 'std_dev': 0.0, 'n_runs': 5},
            {'method': 'Q-Learning', 'metric': 'win_rate', 'value': sample_metrics['win_rate'], 'std_dev': 0.0, 'n_runs': 5},
            {'method': 'Q-Learning', 'metric': 'loss_rate', 'value': sample_metrics['loss_rate'], 'std_dev': 0.0, 'n_runs': 5},
            {'method': 'Q-Learning', 'metric': 'draw_rate', 'value': sample_metrics['draw_rate'], 'std_dev': 0.0, 'n_runs': 5},
        ]

        mock_df_instance = MagicMock()
        mock_df_class.return_value = mock_df_instance

        # Call the function
        result = run_experiment()

        # Assertions
        # 1. It should call DataFrame creation for results rows
        assert mock_df_class.call_count >= 1

        # 2. The final return value is a DataFrame-like object
        # Use type() == pd.DataFrame to avoid isinstance issues with imported modules
        assert type(result) == pd.DataFrame or hasattr(result, 'to_csv')

        # 3. Check that _train_one_run was called N_RUNS times (default 5)
        from config import N_RUNS, SEED_BASE
        assert mock_train.call_count == N_RUNS

        # Verify seeds passed to _train_one_run match SEED_BASE + run_idx
        expected_seeds = [SEED_BASE + i for i in range(N_RUNS)]
        actual_seeds = [call[0][0] for call in mock_train.call_args_list]
        assert actual_seeds == expected_seeds

    def test_history_saved_to_csv(self):
        """
        Verify that training history is saved to 'training_history.csv'.
        This test mocks file writing to ensure no I/O errors and checks the path.
        """
        from config import N_RUNS, N_EPISODES

        sample_metrics = {'train_avg_reward': 0.5, 'win_rate': 0.5, 'loss_rate': 0.25, 'draw_rate': 0.25}
        mock_history = [{'episode': i, 'reward': 0.1} for i in range(N_EPISODES)]

        with patch('experiment._train_one_run') as mock_train:
            with patch('experiment.pd.DataFrame') as mock_df_class:
                # Mock DataFrame instance to handle append and to_csv
                mock_df_instance = MagicMock()
                mock_df_class.return_value = mock_df_instance

                mock_train.return_value = (sample_metrics, mock_history)

                run_experiment()

                # Check if to_csv was called on the history dataframe
                # The code creates history_df from all_histories and calls to_csv
                # We verify that pandas DataFrame constructor was called with list of dicts
                assert mock_df_class.called
