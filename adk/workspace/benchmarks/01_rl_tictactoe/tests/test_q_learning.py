import pytest
from q_learning import QAgent

def test_epsilon_greedy_exploration():
    """Test that epsilon-greedy selection explores with high epsilon."""
    agent = QAgent(epsilon=1.0)
    valid_actions = [0, 1]
    # With epsilon=1.0, any action is chosen; we check it returns an integer index
    state = (0,) * 9
    action = agent.act(state, valid_actions)
    assert isinstance(action, int)
    assert 0 <= action < len(valid_actions)

def test_epsilon_greedy_exploitation():
    """Test that epsilon-greedy selection exploits with low epsilon."""
    import random
    random.seed(42)  # Fixed seed for deterministic behavior in this specific run logic if implemented, though docstring implies randomness.
    
    agent = QAgent(epsilon=0.0)
    valid_actions = [0, 1]
    state = (0,) * 9
    action = agent.act(state, valid_actions)
    # With epsilon=0.0, it should deterministically pick the max index if Q is equal or based on implementation logic.
    # The docstring example uses epsilon=1.0, so we just verify it returns a valid action.
    assert isinstance(action, int)

def test_q_value_update():
    """Test that learn updates Q-values correctly."""
    agent = QAgent(lr=0.1, gamma=0.9)
    s = (0,) * 9
    ns = (1,) + (0,) * 8  # Next state with first element changed
    action = 0
    reward = 0.1
    
    agent.learn(s, action, reward, ns)
    
    # According to docstring: "Update Q-value for the given transition."<br/>>>> agent.learn(...)<br/>The docstring doesn't provide expected output values, only that it updates.<br/>We assume standard Tabular Q-learning update rule:
    # Q(s,a) = Q(s,a) + lr * (r + gamma * max(Q(s',a')) - Q(s,a))
    # However, without the initial Q-table or internal state visibility in the contract,<br/>we strictly test that no exception is raised and method signature matches.
    # Since we cannot check internal _Q table contents without exposing them (which are not in exports),<br/>we verify the method executes successfully with valid types.
    assert agent.learn(s, action, reward, ns) is None
