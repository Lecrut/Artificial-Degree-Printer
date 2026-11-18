from env import TicTacToeEnv
import pytest

def test_step():
    """Test that step executes an action and updates the board correctly."""
    env = TicTacToeEnv()
    env.reset()
    new_s, r, d = env.step(4)
    assert new_s[4] == 1
    assert r == 0
    assert d is False
