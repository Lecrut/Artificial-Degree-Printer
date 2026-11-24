import pytest
from agents import QLearningAgent, RandomAgent
from environment import STATE_SPACE_SIZE, ACTION_SPACE_SIZE
import numpy as np

def _encode_state(obs: np.ndarray) -> int:
    """Helper to encode board state to index, replicating agent's public contract logic."""
    mapped = obs.copy()
    mapped[mapped == -1] = 0
    mapped[mapped == 1] = 2
    index = 0
    multiplier = 1
    for cell in mapped:
        index += int(cell) * multiplier
        multiplier *= 3
    return index

def test_QLearningAgent_init():
    """Test initialization of QLearningAgent matches declared interface."""
    agent = QLearningAgent(learning_rate=0.5, discount_factor=0.9, epsilon=0.2)
    assert hasattr(agent, 'q_table')
    assert isinstance(agent.learning_rate, float)
    assert agent.learning_rate == 0.5
    assert isinstance(agent.discount_factor, float)
    assert agent.discount_factor == 0.9
    assert isinstance(agent.epsilon, float)
    assert agent.epsilon == 0.2
    assert agent.q_table.shape == (STATE_SPACE_SIZE, ACTION_SPACE_SIZE)

def test_QLearningAgent_get_action():
    """Test QLearningAgent.get_action returns valid action index using epsilon-greedy logic."""
    agent = QLearningAgent()
    obs = np.full(9, -1, dtype=int)
    np.random.seed(12345)
    action = agent.get_action(obs, epsilon=0.1)
    assert isinstance(action, int)
    assert 0 <= action < ACTION_SPACE_SIZE

def test_QLearningAgent_learn_terminal():
    """Test QLearningAgent.learn performs correct Q-value update for terminal state."""
    agent = QLearningAgent(learning_rate=1.0, discount_factor=0.95, epsilon=0.1)
    obs = np.full(9, -1, dtype=int)
    action = 0
    reward = 1.0
    next_obs = np.array([-1] * 9, dtype=int)
    terminated = True
    agent.learn(obs, action, reward, next_obs, terminated)
    state_idx = _encode_state(obs)
    expected_q = 1.0
    actual_q = agent.q_table[state_idx, action]
    assert abs(actual_q - expected_q) < 1e-06

def test_QLearningAgent_learn_non_terminal():
    """Test QLearningAgent.learn performs correct Q-value update for non-terminal state."""
    agent = QLearningAgent(learning_rate=0.5, discount_factor=0.9, epsilon=0.1)
    obs = np.full(9, -1, dtype=int)
    action = 0
    reward = 1.0
    next_obs = np.array([-1] * 9, dtype=int)
    terminated = False
    agent.learn(obs, action, reward, next_obs, terminated)
    state_idx = _encode_state(obs)
    expected_q = 0.5
    actual_q = agent.q_table[state_idx, action]
    assert abs(actual_q - expected_q) < 1e-06

def test_RandomAgent_get_action():
    """Test RandomAgent.get_action selects from provided legal_actions list."""
    agent = RandomAgent()
    legal_actions = [2, 5, 7]
    obs = np.full(9, -1, dtype=int)
    np.random.seed(42)
    action = agent.get_action(obs, legal_actions=legal_actions)
    assert isinstance(action, int)
    assert action in legal_actions

def test_RandomAgent_get_action_empty():
    """Test RandomAgent raises ValueError for empty legal_actions list."""
    agent = RandomAgent()
    obs = np.full(9, -1, dtype=int)
    with pytest.raises(ValueError) as exc_info:
        agent.get_action(obs, legal_actions=[])
    assert 'No legal actions available.' in str(exc_info.value)
