import os
import sys
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock, call

# Import only what is exposed by the experiment module's interface per specification.
import experiment

def _make_env_mock():
    """Helper to create a TicTacToeEnv mock that simulates a short terminal game."""
    env = MagicMock()
    # Initial empty board
    env.board = np.zeros(9, dtype=np.int32)
    env.current_player = 1
    
    call_counts = {'reset': 0, 'step': 0}
    
    def mock_reset(seed=None, options=None):
        call_counts['reset'] += 1
        # Reset board to empty for a new game
        env.board = np.zeros(9, dtype=np.int32)
        env.current_player = 1
        obs = env.board.copy()
        info = {"turn": env.current_player}
        return obs, info

    def mock_step(action):
        call_counts['step'] += 1
        # Simulate a game that ends in a draw after 9 moves for simplicity
        # Or just terminate immediately to keep tests fast and deterministic.
        # Let's make it terminate on the first step with a draw (0.0 reward)
        # to avoid complex state manipulation in mocks.
        env.board = np.zeros(9, dtype=np.int32) # Reset internal state of mock board
        obs = env.board.copy()
        reward = 0.0
        terminated = True
        truncated = False
        info = {}
        return obs, reward, terminated, truncated, info

    env.reset.side_effect = mock_reset
    env.step.side_effect = mock_step
    
    return env

def _make_agent_mock():
    """Helper to create a QLearningAgent mock."""
    agent = MagicMock()
    agent.q_table = {}
    agent.epsilon = 1.0
    # Default select_action returns the first valid move
    def mock_select_action(state, valid_moves):
        return valid_moves[0] if valid_moves else 0
    agent.select_action.side_effect = mock_select_action
    return agent

def _make_random_agent_mock():
    """Helper to create a RandomAgent mock."""
    agent = MagicMock()
    def mock_get_action(state, valid_moves):
        return valid_moves[0] if valid_moves else 0
    agent.get_action.side_effect = mock_get_action
    return agent

def test_run_experiment_creates_csv_with_correct_columns():
    """
    Verify that run_experiment:
    1. Instantiates the environment and agents.
    2. Writes results.csv.
    3. The CSV contains exactly the required columns: method, metric, value, std_dev, n_runs.
    4. Contains rows for both 'q_learning' and 'baseline' methods with correct metrics.
    """
    with patch('experiment.TicTacToeEnv') as MockEnv, \
         patch('experiment.QLearningAgent') as MockAgent, \
         patch('experiment.RandomAgent') as MockRandomAgent, \
         patch('experiment.TRAIN_EPISODES', 10), \
         patch('experiment.EVAL_EPISODES', 10), \
         patch('experiment.SEED', 42):
        
        mock_env = _make_env_mock()
        MockEnv.return_value = mock_env

        mock_agent = _make_agent_mock()
        MockAgent.return_value = mock_agent

        mock_random = _make_random_agent_mock()
        MockRandomAgent.return_value = mock_random

        # Patch pd.DataFrame to capture the object before it is written to CSV
        captured_df = None
        def capture_to_csv(path, **kwargs):
            nonlocal captured_df
            captured_df = kwargs.get('df', path) # pandas df usually first arg or 'data'
            # Actually, to_csv is called on self. Let's capture via side_effect
            pass 

        with patch.object(pd.DataFrame, 'to_csv', side_effect=capture_to_csv) as mock_to_csv:
            experiment.run_experiment()
            
            # Retrieve the DataFrame passed to to_csv
            # Since we mocked to_csv, we need to inspect what was passed.
            # The call_args of to_csv will have the dataframe instance if we didn't override it completely,
            # but here we captured it manually or can access via call_args.
            # Let's use a simpler capture:
            
        # Reset for next attempt
        captured_df = None
        def save_df(df, path, *args, **kwargs):
            nonlocal captured_df
            captured_df = df
        
        MockEnv.reset.return_value = (np.zeros(9), {})
        with patch('experiment.TicTacToeEnv', return_value=_make_env_mock()) as m_env:
            with patch('experiment.QLearningAgent', return_value=_make_agent_mock()) as m_agent:
                with patch('experiment.RandomAgent', return_value=_make_random_agent_mock()) as m_rand:
                    # We need to catch the DataFrame instance passed to to_csv
                    original_to_csv = pd.DataFrame.to_csv
                    
                    def track_df(self, path_or_buf, **kwargs):
                        nonlocal captured_df
                        captured_df = self
                        return original_to_csv(self, '/dev/null', **kwargs)
                        
                    with patch.object(pd.DataFrame, 'to_csv', side_effect=track_df):
                        experiment.run_experiment()

        # Verify columns
        assert captured_df is not None, "results.csv was not generated (DataFrame not captured)"
        expected_columns = {'method', 'metric', 'value', 'std_dev', 'n_runs'}
        assert set(captured_df.columns) == expected_columns, f"Expected columns {expected_columns}, got {set(captured_df.columns)}"

        # Verify content structure
        data_list = captured_df.to_dict(orient='records')
        methods = [r['method'] for r in data_list]
        metrics = [r['metric'] for r in data_list]
        
        assert 'q_learning' in methods, "Missing 'q_learning' method row"
        assert 'baseline' in methods, "Missing 'baseline' method row"
        
        # Check specific metrics exist
        ql_metrics = [r['metric'] for r in data_list if r['method'] == 'q_learning']
        expected_ql_metrics = {'win_rate', 'draw_rate', 'loss_rate', 'avg_reward'}
        assert set(ql_metrics) == expected_ql_metrics, f"QLearning metrics mismatch: {set(ql_metrics)} vs {expected_ql_metrics}"
        
        bl_metrics = [r['metric'] for r in data_list if r['method'] == 'baseline']
        expected_bl_metrics = {'win_rate', 'draw_rate', 'loss_rate'}
        assert set(bl_metrics) == expected_bl_metrics, f"Baseline metrics mismatch: {set(bl_metrics)} vs {expected_bl_metrics}"

        # Verify agent methods were called during training
        # Note: With mocks, exact call counts depend on mock setup. We just verify they were invoked.
        assert mock_agent.select_action.called, "Agent select_action was not called during training/eval"
        assert mock_agent.update.called, "Agent update was not called during training"
        assert mock_rand.get_action.called, "Random agent get_action was not called during eval"

def test_run_experiment_metrics_value_types():
    """
    Verify that the 'value' and 'std_dev' columns in results.csv contain numeric types (float),
    and 'method', 'metric', 'n_runs' are strings/int appropriately.
    """
    captured_df = None
    def track_df(self, path_or_buf, **kwargs):
        nonlocal captured_df
        captured_df = self
    
    with patch('experiment.TicTacToeEnv', return_value=_make_env_mock()) as m_env:
        with patch('experiment.QLearningAgent', return_value=_make_agent_mock()) as m_agent:
            with patch('experiment.RandomAgent', return_value=_make_random_agent_mock()) as m_rand:
                with patch.object(pd.DataFrame, 'to_csv', side_effect=track_df):
                    experiment.run_experiment()

    assert captured_df is not None
    
    # Check value column types
    assert pd.api.types.is_float_dtype(captured_df['value']), f"'value' column should be float, got {captured_df['value'].dtype}"
    
    # Check method and metric are strings
    assert pd.api.types.is_string_dtype(captured_df['method']), "'method' column should be string"
    assert pd.api.types.is_string_dtype(captured_df['metric']), "'metric' column should be string"
    
    # Check n_runs is int
    assert pd.api.types.is_integer_dtype(captured_df['n_runs']), "'n_runs' column should be integer"
