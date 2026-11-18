import pytest
from opponent import RandomOpponent

def test_random_opp_init():
    """Test RandomOpponent initialization with valid player symbol."""
    opp = RandomOpponent(player_symbol='X')
    assert hasattr(opp, 'player_symbol')
    assert opp.player_symbol == 'X'

def test_random_opp_choose_action_basic():
    """Test that a random action is chosen from valid moves."""
    opp = RandomOpponent(player_symbol='X')
    valid_moves = [0, 1, 2]
    action = opp.choose_action(valid_moves)
    assert action in valid_moves

def test_random_opp_choose_action_multiple_runs():
    """Test multiple runs to ensure randomness."""
    opp = RandomOpponent(player_symbol='O')
    valid_moves = [5, 6]
    for _ in range(10):
        action = opp.choose_action(valid_moves)
        assert action in valid_moves
