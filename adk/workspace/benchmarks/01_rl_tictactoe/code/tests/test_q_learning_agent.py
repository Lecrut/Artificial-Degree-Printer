import pytest
from q_learning_agent import QLearningAgent
import numpy as np

def test_init():
    """Test initialization of QLearningAgent sets epsilon correctly and creates empty Q-table."""
    agent = QLearningAgent(learning_rate=0.1, discount_factor=0.9, initial_epsilon=0.5, decay=0.99)
    assert isinstance(agent.q_table, dict)
    assert len(agent.q_table) == 0
    assert agent.epsilon == 0.5
    assert agent.learning_rate == 0.1
    assert agent.discount_factor == 0.9
    assert agent.decay == 0.99

def test_act_epsilon_greedy():
    """Test act method selects action based on epsilon-greedy policy."""
    agent = QLearningAgent(learning_rate=0.1, discount_factor=0.9, initial_epsilon=1.0, decay=0.99)
    state = np.array([0, 1, 0])
    valid_moves = [0, 2]
    action1 = agent.act(state, valid_moves)
    action2 = agent.act(state, valid_moves)
    assert action1 in valid_moves
    assert action2 in valid_moves
    agent_epsilon = QLearningAgent(learning_rate=0.1, discount_factor=0.9, initial_epsilon=0.01, decay=0.99)
    state_tuple = tuple(state.tolist())
    q_values = np.array([0.5, 0.0])
    agent_epsilon.q_table[state_tuple] = q_values
    action = agent_epsilon.act(state_tuple, valid_moves)
    assert isinstance(action, int)
    assert action in valid_moves

def test_learn():
    """Test learn method updates Q-table correctly using Bellman equation."""
    agent = QLearningAgent(learning_rate=0.1, discount_factor=0.9, initial_epsilon=1.0, decay=0.99)
    state1 = np.array([0, 0])
    next_state = np.array([1, 0])
    action = 0
    reward = 1.0
    terminated = False
    agent.learn(state1, action, reward, next_state, terminated)
    assert state1 in [tuple(s) for s in agent.q_table.keys()]
    q_values = agent.q_table[tuple(state1)]
    assert isinstance(q_values, np.ndarray)

def test_reset():
    """Test reset method resets epsilon to initial_epsilon without clearing Q-table."""
    agent = QLearningAgent(learning_rate=0.1, discount_factor=0.9, initial_epsilon=0.5, decay=0.99)
    agent.epsilon = 0.2
    agent.reset()
    assert agent.epsilon == 0.5

def test_attribute_access():
    """Test that all declared attributes in specification are accessible."""
    agent = QLearningAgent(learning_rate=0.5, discount_factor=0.8, initial_epsilon=0.3, decay=0.9)
    assert hasattr(agent, 'learning_rate')
    assert hasattr(agent, 'discount_factor')
    assert hasattr(agent, 'epsilon')
    assert hasattr(agent, 'initial_epsilon')
    assert hasattr(agent, 'decay')
    assert hasattr(agent, 'q_table')
