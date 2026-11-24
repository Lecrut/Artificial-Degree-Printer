from agent import QLearningAgent
import numpy as np

def test_initialization_parameters():
    """Test that __init__ sets attributes correctly and accepts required parameters."""
    alpha = 0.5
    gamma = 0.9
    epsilon = 0.1
    agent = QLearningAgent(alpha, gamma, epsilon)
    assert agent.alpha == alpha
    assert agent.gamma == gamma
    assert agent.epsilon == epsilon
    assert isinstance(agent.q_table, dict)

def test_select_action_epsilon_greedy():
    """Test select_action chooses random move when epsilon allows exploration."""
    agent = QLearningAgent(0.5, 0.9, 1.0)
    state = (0,)
    valid_moves = [0, 1, 2]
    action = agent.select_action(state, valid_moves)
    assert action in valid_moves

def test_select_action_exploitation():
    """Test select_action chooses max Q-value when epsilon=0."""
    agent = QLearningAgent(0.5, 0.9, 0.0)
    state = (1,)
    valid_moves = [1, 2]
    q_values = agent.get_q_values(state)
    q_values[1] = 1.0
    q_values[2] = 0.5
    action = agent.select_action(state, valid_moves)
    assert action == 1

def test_update_q_learning_rule():
    """Test the update logic follows Q(s,a) <- Q + alpha*(reward + gamma*max_next - Q)."""
    agent = QLearningAgent(0.5, 0.9, 0.0)
    state = (2,)
    action = 0
    reward = 10.0
    next_state = (3,)
    done = False
    q_vals = agent.get_q_values(state)
    assert np.all(q_vals == 0.0)
    agent.update(state, action, reward, next_state, done)
    expected_value = 0.0 + 0.5 * (10.0 + 0.9 * 0.0 - 0.0)
    assert agent.q_table[state][action] == expected_value

def test_update_done_case():
    """Test update handles done=True correctly (no future rewards)."""
    agent = QLearningAgent(0.5, 0.9, 0.0)
    state = (4,)
    action = 0
    reward = 0
    next_state = (5,)
    done = True
    agent.update(state, action, reward, next_state, done)
    assert agent.q_table[state][action] == 0.0

def test_get_q_values_initialization():
    """Test get_q_values initializes new state to zeros."""
    agent = QLearningAgent(0.5, 0.9, 0.0)
    new_state = (10,)
    q_vals = agent.get_q_values(new_state)
    assert isinstance(q_vals, np.ndarray)
    assert len(q_vals) == 9
    assert np.all(q_vals == 0.0)

def test_update_with_existing_entry():
    """Test update modifies existing Q-value correctly."""
    agent = QLearningAgent(0.5, 0.9, 0.0)
    state = (2,)
    action = 0
    reward = 1.0
    next_state = (3,)
    done = False
    agent.q_table[state] = np.zeros(9)
    agent.q_table[state][action] = 2.0
    agent.update(state, action, reward, next_state, done)
    expected = 1.5
    assert agent.q_table[state][action] == expected
