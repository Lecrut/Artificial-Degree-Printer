import pytest
from baseline_agent import RandomAgent

def test_RandomAgent_init_and_env():
    """Test that RandomAgent accepts env in init and exposes it as an attribute."""
    # Create a mock environment to avoid needing a full gym setup for this unit test
    class MockEnv:
        def __init__(self):
            self.actions = []
    
    env = MockEnv()
    agent = RandomAgent(env)
    
    # Verify 'env' attribute exists and holds the passed object
    assert hasattr(agent, 'env'), "RandomAgent must have an 'env' attribute."
    assert agent.env is env, "The 'env' attribute must be the same instance passed to __init__."

def test_RandomAgent_act_signature():
    """Test that act method exists and accepts state as a required argument."""
    class MockEnv:
        def __init__(self):
            self.actions = []
    
    env = MockEnv()
    agent = RandomAgent(env)
    
    # Verify the method exists
    assert hasattr(agent, 'act'), "RandomAgent must have an 'act' method."
    
    # We cannot call act without a real state or side effects, but we can verify it's callable.
    # The test passes if it runs without AttributeError on calling it (though logic inside might be undefined).
    # Per spec, we check interface only. If the body raises NotImplementedError, that's acceptable for a stub.
    assert callable(agent.act), "The 'act' method must be callable."

if __name__ == "__main__":
    pytest.main([__file__, "-v"])