import pytest
import numpy as np
from baseline import RandomAgent

def test_random_agent_initialization() -> None:
    """Tests that the RandomAgent can be instantiated and has no required attributes."""
    agent = RandomAgent()
    assert isinstance(agent, RandomAgent)

def test_choose_action_valid_actions() -> None:
    """Tests that choosing an action from a list of valid actions returns a valid index."""
    agent = RandomAgent()
    rng = np.random.default_rng(42)
    valid_actions = [0]
    chosen_action = agent.choose_action(valid_actions, rng)
    assert chosen_action == 0
    valid_actions = [0, 1, 2]
    np.random.seed(123)
    chosen_0 = agent.choose_action(valid_actions, np.random.default_rng(42))
    chosen_1 = agent.choose_action(valid_actions, np.random.default_rng(43))
    assert isinstance(chosen_0, int)
    assert 0 <= chosen_0 < len(valid_actions)
    assert isinstance(chosen_1, int)
    assert 0 <= chosen_1 < len(valid_actions)

def test_choose_action_empty_valid_actions() -> None:
    """Tests that choosing an action from an empty list raises ValueError."""
    agent = RandomAgent()
    with pytest.raises(ValueError) as context:
        agent.choose_action([], np.random.default_rng(42))
    assert 'high <= 0' in str(context.value)
