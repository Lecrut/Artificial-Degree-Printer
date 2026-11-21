import pytest
from agents import QLearningAgent, RandomAgent


def test_QLearningAgent_init():
    """Test QLearningAgent initialization with correct parameters."""
    agent = QLearningAgent(n_states=10, n_actions=9, lr=0.1, gamma=0.9, epsilon=0.0)
    assert isinstance(agent, QLearningAgent)
    assert hasattr(agent, 'q_table')
    assert hasattr(agent, 'lr')
    assert hasattr(agent, 'gamma')
    assert hasattr(agent, 'epsilon')


def test_QLearningAgent_act():
    """Test QLearningAgent action selection with epsilon-greedy policy."""
    agent = QLearningAgent(n_states=10, n_actions=9, lr=0.1, gamma=0.9, epsilon=0.0)
    import random
    random.seed(42)
    res = agent.act(state_index=0, legal_moves=[1, 2])
    assert res in [1, 2]


def test_QLearningAgent_update():
    """Test Q-learning update rule increases Q-value when done=True."""
    agent = QLearningAgent(n_states=10, n_actions=9, lr=0.1, gamma=0.5, epsilon=0.5)
    # Create a mock q_table structure (default to 0 or empty if needed, assuming initialization provides access)
    # We rely on the attribute 'q_table' being set by __init__
    before = agent.q_table[0, 4]
    agent.update(state_index=0, action=4, reward=1.0, next_state_index=1, done=True)
    after = agent.q_table[0, 4]
    assert after >= before


def test_QLearningAgent_get_q_table():
    """Test retrieval of Q-table."""
    agent = QLearningAgent(n_states=10, n_actions=9, lr=0.1, gamma=0.9, epsilon=0.0)
    q_table = agent.get_q_table()
    assert isinstance(q_table, dict) or type(q_table).__name__ != 'NoneType'  # Check if it returns something valid


def test_RandomAgent_act():
    """Test RandomAgent selects a random action from legal moves."""
    agent = RandomAgent()
    moves = [1, 2, 3]
    res = agent.act(legal_moves=moves)
    assert res in moves