from environment import TicTacToeEnv
import pytest

def test_reset_initial_state():
    """Test that reset returns an initial empty board state (9 zeros)."""
    env = TicTacToeEnv()
    state = env.reset()
    assert isinstance(state, tuple)
    assert len(state) == 9
    assert all((s == 0 for s in state))

def test_step_updates_state():
    """Test that step places the action on the board correctly."""
    env = TicTacToeEnv()
    state = env.reset()
    next_s, r, d = env.step(4, 1)
    assert isinstance(next_s, tuple)
    assert next_s[4] == 1

def test_get_valid_actions_empty_board():
    """Test that get_valid_actions returns all indices on an empty board."""
    env = TicTacToeEnv()
    state = env.reset()
    actions = env.get_valid_actions(state)
    assert isinstance(actions, list)
    assert len(actions) == 9
    assert set(actions) == {0, 1, 2, 3, 4, 5, 6, 7, 8}

def test_is_terminal_empty_board():
    """Test that is_terminal returns False on a non-terminal state."""
    env = TicTacToeEnv()
    state = env.reset()
    result = env.is_terminal(state)
    assert isinstance(result, bool)
    assert not result

def test_check_win_player_x():
    """Test that check_win detects a win for player X (1)."""
    state = (1, 1, 1, 0, 0, 0, 0, 0, 0)
    env = TicTacToeEnv()
    result = env.check_win(state, 1)
    assert isinstance(result, bool)
    assert result

def test_check_win_player_o():
    """Test that check_win detects a win for player O (-1)."""
    state = (0, -1, 0, 0, -1, 0, 0, 0, -1)
    env = TicTacToeEnv()
    result = env.check_win(state, -1)
    assert isinstance(result, bool)
    assert result
