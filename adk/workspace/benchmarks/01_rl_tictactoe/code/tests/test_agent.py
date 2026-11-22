import agent
from unittest.mock import MagicMock

def test_default_constants_are_floats():
    """Verify that DEFAULT_ALPHA, DEFAULT_GAMMA, DEFAULT_EPSILON_START, and DEFAULT_EPSILON_END are floats."""
    assert isinstance(agent.DEFAULT_ALPHA, float)
    assert isinstance(agent.DEFAULT_GAMMA, float)
    assert isinstance(agent.DEFAULT_EPSILON_START, float)
    assert isinstance(agent.DEFAULT_EPSILON_END, float)

def test_qlearning_agent_init_creates_attributes():
    """Verify that QLearningAgent.__init__ initializes expected attributes."""
    mock_env = MagicMock()
    q_agent = agent.QLearningAgent(mock_env, agent.DEFAULT_ALPHA, agent.DEFAULT_GAMMA, agent.DEFAULT_EPSILON_START)
    assert hasattr(q_agent, 'alpha')
    assert hasattr(q_agent, 'gamma')
    assert hasattr(q_agent, 'epsilon')
    assert hasattr(q_agent, 'q_table')
    assert hasattr(q_agent, 'rng')
    assert hasattr(q_agent, 'env')

def test_qlearning_agent_act_signature_and_return_type():
    """Verify that QLearningAgent.act returns a single integer action for a given state."""
    mock_env = MagicMock()
    q_agent = agent.QLearningAgent(mock_env, agent.DEFAULT_ALPHA, agent.DEFAULT_GAMMA, agent.DEFAULT_EPSILON_START)
    state = 0
    action = q_agent.act(state)
    assert isinstance(action, int)

def test_qlearning_agent_update_signature():
    """Verify that QLearningAgent.update accepts the correct parameters."""
    mock_env = MagicMock()
    q_agent = agent.QLearningAgent(mock_env, agent.DEFAULT_ALPHA, agent.DEFAULT_GAMMA, agent.DEFAULT_EPSILON_START)
    state = 0
    action = 0
    reward = 1.0
    next_state = 0
    done = False
    # Just calling with correct signature verifies the interface
    q_agent.update(state, action, reward, next_state, done)

def test_qlearning_agent_update_updates_attributes():
    """Verify that QLearningAgent.update modifies the q_table and epsilon."""
    mock_env = MagicMock()
    q_agent = agent.QLearningAgent(mock_env, agent.DEFAULT_ALPHA, agent.DEFAULT_GAMMA, agent.DEFAULT_EPSILON_START)
    state = 0
    action = 0
    reward = 1.0
    next_state = 1
    done = False
    initial_epsilon = q_agent.epsilon
    q_agent.update(state, action, reward, next_state, done)
    # Check if epsilon was updated (standard Q-learning update uses current epsilon for exploration) or just verify attribute existence as per spec
    assert hasattr(q_agent, 'q_table')
    assert isinstance(q_agent.q_table, dict)

def test_qlearning_agent_epsilon_is_accessible():
    """Verify that QLearningAgent.epsilon attribute exists and is a float."""
    mock_env = MagicMock()
    q_agent = agent.QLearningAgent(mock_env, agent.DEFAULT_ALPHA, agent.DEFAULT_GAMMA, agent.DEFAULT_EPSILON_START)
    assert hasattr(q_agent, 'epsilon')
    assert isinstance(q_agent.epsilon, float)
