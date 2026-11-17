import pytest
from baseline import RandomAgent


def test_random_agent_returns_valid_action():
    """Test that RandomAgent.act returns an action from the provided valid_actions list."""
    valid = [0, 1]
    agent = RandomAgent()
    # Just ensures it returns one of the valid actions
    res = agent.act((0,)*9, valid)
    assert res in valid