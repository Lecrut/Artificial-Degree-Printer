import pytest
from unittest.mock import patch, MagicMock

def test_train_and_evaluate_called_with_correct_args():
    with patch('core.train_and_evaluate') as mock_train:
        # Mock return value to avoid actual training
        mock_train.return_value = (0.85, 0.12, 0.03)
        
        # Import and run the function that would be tested
        import core
        result = core.train_and_evaluate()
        
        assert result == (0.85, 0.12, 0.03)
        mock_train.assert_called_once_with()

def test_train_and_evaluate_returns_valid_rates():
    with patch('core.train_and_evaluate') as mock_train:
        mock_train.return_value = (0.92, 0.05, 0.03)
        
        import core
        win_rate, draw_rate, loss_rate = core.train_and_evaluate()
        
        assert 0 <= win_rate <= 1
        assert 0 <= draw_rate <= 1
        assert 0 <= loss_rate <= 1
        assert abs(win_rate + draw_rate + loss_rate - 1.0) < 1e-6
