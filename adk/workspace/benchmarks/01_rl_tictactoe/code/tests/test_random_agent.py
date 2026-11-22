from agents.random_agent import RandomAgent
import pytest


def test_name_is_attribute():
    """Verify that 'name' is a declared attribute of RandomAgent."""
    agent = RandomAgent()
    # Assert on the declared attribute as per specification
    assert hasattr(RandomAgent, 'name') or (isinstance(agent, RandomAgent) and hasattr(agent, 'name'))


def test_act_signature_and_behavior():
    """Verify that act method returns exactly one action from valid_actions."""
    agent = RandomAgent()
    state = None  # State is required by signature but behavior depends on valid_actions
    valid_actions = [0, 1, 2]
    
    # Call act with the declared parameters
    action = agent.act(state=state, valid_actions=valid_actions)
    
    # Check that the returned action exists in valid_actions (behavioral contract)
    assert action in valid_actions
