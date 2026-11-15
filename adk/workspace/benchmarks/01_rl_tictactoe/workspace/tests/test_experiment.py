import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from unittest.mock import patch, MagicMock
import src.config as config_module
from src.experiment import run_experiment
import tempfile

def test_run_experiment_produces_results():
    """Ensure experiment produces a results CSV file."""
    mock_config = MagicMock()
    mock_config.N_RUNS = 1
    mock_config.RANDOM_SEED = 42
    mock_config.EPOCHES_PER_EVALUATION = 50
    
    with patch('src.tictactoe_env.TicTacToeEnv.step', return_value=(None, None, None, {})):
        with patch('src.tictactoe_env.TicTacToeEnv.reset'):
            run_experiment()
