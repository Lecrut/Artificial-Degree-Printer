import pytest
from unittest.mock import patch, MagicMock

def test_train_and_evaluate_function_exists():
    from core import train_and_evaluate
    assert callable(train_and_evaluate)

def test_train_and_evaluate_returns_correct_structure():
    from core import train_and_evaluate
    result = train_and_evaluate()
    assert isinstance(result, dict)
    assert 'win_rate' in result
    assert 'draw_rate' in result
    assert 'loss_rate' in result

def test_train_and_evaluate_with_mocked_data():
    from core import train_and_evaluate
    
    with patch('core.load_data', return_value=MagicMock()):
        with patch('core.process_episodes', return_value=(0.85, 0.10, 0.05)):
            result = train_and_evaluate()
            assert isinstance(result['win_rate'], float)
            assert isinstance(result['draw_rate'], float)
            assert isinstance(result['loss_rate'], float)
