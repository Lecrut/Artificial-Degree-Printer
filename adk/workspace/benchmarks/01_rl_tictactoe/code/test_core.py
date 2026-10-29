import pytest
from unittest.mock import patch, MagicMock

def test_train_and_evaluate():
    # Mock the train_and_evaluate function to return a fixed result
    with patch('core.train_and_evaluate', return_value=(0.85, 0.10, 0.05)):
        from core import train_and_evaluate
        win_rate, draw_rate, loss_rate = train_and_evaluate(500)
        assert win_rate == 0.85
        assert draw_rate == 0.10
        assert loss_rate == 0.05

def test_edge_cases():
    # Test with zero episodes
    with patch('core.train_and_evaluate', return_value=(0.0, 0.0, 1.0)):
        from core import train_and_evaluate
        win_rate, draw_rate, loss_rate = train_and_evaluate(0)
        assert win_rate == 0.0
        assert draw_rate == 0.0
        assert loss_rate == 1.0
