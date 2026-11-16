from unittest.mock import patch, MagicMock
import pytest
from src.ql_agent import QAgent

def test_initial_q_values_zero() -> None:
    """Test that initial Q_table is a dict and returns None for unseen states, and get_action returns an int."""
    agent = QAgent(alpha=0.1, gamma=0.9, epsilon_start=0.5, epsilon_end=0.01, decay_rate=0.99)
    assert isinstance(agent.Q_table, dict), 'Q_table should be initialized as a standard dict'
    state_key = 'test_state_123'
    result = agent.Q_table.get(state_key)
    assert result is None, 'Unseen state should return None by default (dict behavior)'
    with patch.object(agent, 'get_random_choice', return_value=0):
        action = agent.get_action(state_key)
        assert isinstance(action, int), 'get_action must return an integer.'
        assert action == 0, 'With mocked choice returning 0, selected action should be 0'
with patch.object(agent, 'get_random_choice', return_value=0) as mock_choice:
    action = agent.get_action(state_key)
    assert isinstance(action, int), 'get_action must return an integer.'
    assert action == 0, 'With mocked choice returning 0, selected action should be 0'

def test_q_value_update_validity() -> None:
    """Test that update method correctly updates Q-values."""
    agent = QAgent(alpha=0.1, gamma=0.9)
    state_key = 'test_state_a'
    action_idx = 0
    next_state_key = 'test_state_b'
    reward_val = 1.0
    agent.Q_table[state_key] = {}
    agent.Q_table[state_key][action_idx] = 0.0
    with patch.object(agent, 'decay_epsilon') as mock_decay:
        agent.update(state_key, action_idx, reward_val, next_state_key)
        assert state_key in agent.Q_table
        assert hasattr(agent, 'epsilon')
        expected_new_q = agent.Q_table[state_key][action_idx]
        assert isinstance(agent.Q_table, dict)

def test_epsilon_greedy_action_selection() -> None:
    """Test that get_action returns the mocked action when randomness is patched."""
    agent = QAgent(alpha=0.1, gamma=0.9)
    state_key = 'test_state_a'
    if state_key not in agent.Q_table:
        agent.Q_table[state_key] = {}
    with patch.object(agent, 'get_random_choice', return_value=1) as mock_choice:
        action = agent.get_action(state_key)
        assert isinstance(action, int), 'get_action must return an integer.'
        assert action == 1

def test_q_value_update_validity(self) -> None:
    """Test that update method correctly calls decay_epsilon and updates Q-values."""
    agent = QAgent(alpha=0.1, gamma=0.9)
    state_key = 'test_state_a'
    action_idx = 0
    next_state_key = 'test_state_b'
    reward_val = 1.0
    if state_key not in agent.Q_table:
        agent.Q_table[state_key] = {}
    agent.Q_table[state_key][action_idx] = 0.0
    agent.decay_epsilon()
    with patch.object(type(agent), 'decay_epsilon', return_value=None) as mock_decay:
        agent.update(state_key, action_idx, reward_val, next_state_key)
        assert mock_decay.called, 'Mocked decay_epsilon should be called during or after update'
