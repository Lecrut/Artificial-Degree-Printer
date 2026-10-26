import pytest
from unittest.mock import patch, MagicMock

def test_train_and_evaluate_function_exists():
    from core import train_and_evaluate
    assert callable(train_and_evaluate)

def test_train_and_evaluate_returns_correct_format():
    from core import train_and_evaluate
    
    # Mock the config to avoid actual training
    with patch('core.FEDERATED_LEARNING_CONFIG', {}), \
         patch('core.MODEL_HYPERPARAMETERS', {}), \
         patch('core.TRAINING_CONFIG', {}):
        
        result = train_and_evaluate(method='baseline', episodes=100)
        
        assert isinstance(result, dict)
        assert 'win_rate' in result
        assert 'draw_rate' in result
        assert 'loss_rate' in result
        assert 'episodes' in result

def test_train_and_evaluate_handles_edge_cases():
    from core import train_and_evaluate
    
    # Test with zero episodes
    with patch('core.FEDERATED_LEARNING_CONFIG', {}), \
         patch('core.MODEL_HYPERPARAMETERS', {}), \
         patch('core.TRAINING_CONFIG', {}):
        
        result = train_and_evaluate(method='baseline', episodes=0)
        assert result['episodes'] == 0

def test_train_and_evaluate_consistent_output():
    from core import train_and_evaluate
    
    with patch('core.FEDERATED_LEARNING_CONFIG', {}), \
         patch('core.MODEL_HYPERPARAMETERS', {}), \
         patch('core.TRAINING_CONFIG', {}):
        
        result1 = train_and_evaluate(method='baseline', episodes=50)
        result2 = train_and_evaluate(method='baseline', episodes=50)
        
        assert result1['win_rate'] == result2['win_rate']
        assert result1['draw_rate'] == result2['draw_rate']
        assert result1['loss_rate'] == result2['loss_rate']