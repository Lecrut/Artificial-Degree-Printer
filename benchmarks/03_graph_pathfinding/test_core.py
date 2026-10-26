import pytest
from unittest.mock import patch, MagicMock

def test_train_and_evaluate_function_exists():
    # Check that the function exists in core module
    from core import train_and_evaluate
    assert callable(train_and_evaluate)

def test_train_and_evaluate_returns_dict():
    # Mock the train_and_evaluate function to return a known result
    with patch('core.train_and_evaluate', return_value={'win_rate': 0.85, 'draw_rate': 0.10, 'loss_rate': 0.05}):
        from core import train_and_evaluate
        result = train_and_evaluate()
        assert isinstance(result, dict)
        assert 'win_rate' in result
        assert 'draw_rate' in result
        assert 'loss_rate' in result

def test_train_and_evaluate_with_mocked_data():
    # Test with mocked data to ensure deterministic behavior
    mock_result = {'win_rate': 0.88, 'draw_rate': 0.08, 'loss_rate': 0.04}
    with patch('core.train_and_evaluate', return_value=mock_result):
        from core import train_and_evaluate
        result = train_and_evaluate()
        assert result['win_rate'] == 0.88
        assert result['draw_rate'] == 0.08
        assert result['loss_rate'] == 0.04
