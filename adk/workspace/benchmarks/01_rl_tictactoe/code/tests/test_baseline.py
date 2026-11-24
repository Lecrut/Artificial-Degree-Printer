import pytest
from baseline import RandomAgent
import numpy as np

def test_random_agent_init() -> None:
    """Test that RandomAgent initializes without internal state.

    The interface declares __init__ takes no arguments besides self,
    and the agent should have no internal state to track game history.
    """
    agent = RandomAgent()
    # Verify initialization completes successfully
    assert agent is not None

def test_random_agent_get_action_basic() -> None:
    """Test that get_action selects a random valid move uniformly.

    The interface specifies:
        - state: 3x3 numpy array (unused in logic but required)
        - valid_moves: list[int] of indices to choose from
        - Returns: int index chosen from valid_moves
    
    This test verifies the return value is always present in valid_moves.
    """
    agent = RandomAgent()
    # Provide a sample board with 3 valid moves (indices 0, 1, 2)
    state = np.zeros((3, 3), dtype=int)
    valid_moves = [0, 1, 2]
    
    chosen_move = agent.get_action(state, valid_moves)
    
    # The return value must be an integer present in the provided valid moves
    assert isinstance(chosen_move, int)
    assert chosen_move in valid_moves

def test_random_agent_get_action_value_error() -> None:
    """Test that get_action raises ValueError when valid_moves is empty.

    The interface documentation explicitly states: "If `valid_moves` is empty,
    raises ValueError..."
    """
    agent = RandomAgent()
    state = np.zeros((3, 3), dtype=int)
    valid_moves = []
    
    with pytest.raises(ValueError):
        agent.get_action(state, valid_moves)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])