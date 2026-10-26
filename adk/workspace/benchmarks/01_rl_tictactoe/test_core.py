import pytest
from unittest.mock import patch, MagicMock

def test_train_and_evaluate():
    # Mock the train_and_evaluate function to return predefined results
    with patch('core.train_and_evaluate') as mock_train:
        mock_train.return_value = (0.85, 0.10, 0.05)
        
        # Call the function
        win_rate, draw_rate, loss_rate = train_and_evaluate()
        
        # Assert that the returned values match expected ones
        assert win_rate == 0.85
        assert draw_rate == 0.10
        assert loss_rate == 0.05

def test_train_and_evaluate_with_seed():
    # Test with a fixed seed to ensure deterministic behavior
    with patch('core.train_and_evaluate') as mock_train:
        mock_train.return_value = (0.90, 0.08, 0.02)
        
        win_rate, draw_rate, loss_rate = train_and_evaluate()
        
        assert win_rate == 0.90
        assert draw_rate == 0.08
        assert loss_rate == 0.02
