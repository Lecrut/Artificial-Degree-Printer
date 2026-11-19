from ttt_agent import Agent
import numpy as np
import pytest

def test_init_attributes():
    """Test that all public attributes are initialized correctly."""
    a = Agent(0.1, 0.9, 1.0, 0.01, 0.995, 42)
    assert a.lr == 0.1
    assert a.gamma == 0.9
    assert a.epsilon_start == 1.0
    assert a.epsilon_end == 0.01
    assert a.epsilon_decay == 0.995
    assert a.q_table is not None
    assert a.epsilon == 1.0

def test_reset():
    """Test that reset initializes the board and resets epsilon."""
    a = Agent(0.1, 0.9, 1.0, 0.01, 0.995, 42)
    a.reset()
    # Ensure Q-table is empty or zero-filled (behavior inferred from context, checking length via get_q_values)
    q_vals = a.get_q_values("0" * 9)
    assert len(q_vals) == 9

def test_get_q_values_empty_table():
    """Test that unvisited states return zeros for empty Q-table."""
    a = Agent(0.1, 0.9, 1.0, 0.01, 0.995, 42)
    state = "0" * 9
    q_vals = a.get_q_values(state)
    # Docstring example implies returning zeros for unvisited states
    assert all(q == 0.0 for q in q_vals)

def test_get_q_values_with_entries():
    """Test that existing Q-values are retrieved correctly."""
    a = Agent(0.1, 0.9, 1.0, 0.01, 0.995, 42)
    
    # Update with dummy data to populate the table
    state = "111000000"
    action_idx = 0
    reward = 1.0
    next_state = "000111000" # dummy
    done = False
    
    a.update(state, action_idx, reward, next_state, done)
    
    q_vals = a.get_q_values(state)
    assert len(q_vals) == 9
    # Only the updated index should have a non-zero value in this simple scenario
    assert abs(q_vals[action_idx]) > 0.5

def test_choose_action_empty():
    """Test action selection with epsilon-greedy logic on fresh agent."""
    a = Agent(0.1, 0.9, 1.0, 0.01, 0.995, 42)
    state_hash = "0" * 9
    legal_moves = [0, 1, 2, 3, 4, 5, 6, 7, 8]
    
    action = a.choose_action(state_hash, legal_moves, epsilon=1.0)
    
    assert action in legal_moves
    # With epsilon=1.0 (exploration max), it might pick randomly, so we check validity only

def test_decay_epsilon():
    """Test that epsilon decreases after update."""
    a = Agent(0.1, 0.9, 1.0, 0.01, 0.995, 42)
    initial_eps = a.epsilon
    
    # Trigger decay by doing one step (epsilon is typically decayed after update in Q-learning loops)
    state = "1" * 9
    action = 0
    reward = 0
    next_state = "0" * 9
    done = False
    a.update(state, action, reward, next_state, done)
    
    decayed_eps = a.epsilon
    expected_new_eps = initial_eps * a.epsilon_decay
    
    assert abs(decayed_eps - expected_new_eps) < 1e-6