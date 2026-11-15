import pytest as play_test
from src.tictactoe_env import TicTacToeEnv
import numpy as np

@pytest.fixture(autouse=True)
def fresh_env():
    """Ensure every test starts with a clean environment to prevent state leakage."""
    env = TicTacToeEnv()
    env.reset()
    return env

def test_initial_state_is_valid(fresh_env: TicTacToeEnv) -> None:
    s, r = fresh_env.reset()
    assert isinstance(s, np.ndarray), 'Initial state must be a numpy array'
    assert s.shape == (9,), f'Initial state shape must be (9,), got {s.shape}'
    assert not fresh_env.is_game_over(), 'Game should not be over at start'

def test_invalid_move_raises_error(fresh_env: TicTacToeEnv) -> None:
    with play_test.raises(ValueError):
        fresh_env.step(9)
    with play_test.raises(ValueError):
        fresh_env.step(-1)

def test_win_detection_horizontal(fresh_env: TicTacToeEnv) -> None:
    s, r, d, info = fresh_env.step(6)
    assert not d
    assert fresh_env.is_game_over() is False
    s, r, d, info = fresh_env.step(0)
    assert not d
    s, r, d, info = fresh_env.step(7)
    assert not d
    s, r, d, info = fresh_env.step(1)
    assert not d
    s, r, d, info = fresh_env.step(8)
    assert d, 'Game should end after X wins horizontal'
    assert info.get('winner') == 'X', f"Expected winner X, got {info.get('winner')}"

def test_win_detection_vertical(fresh_env: TicTacToeEnv) -> None:
    s, r, d, info = fresh_env.step(0)
    assert not d
    assert fresh_env.is_game_over() is False
    s, r, d, info = fresh_env.step(8)
    assert not d
    s, r, d, info = fresh_env.step(3)
    assert not d
    s, r, d, info = fresh_env.step(7)
    assert not d
    s, r, d, info = fresh_env.step(6)
    assert d, 'Game should end after X wins vertical'
    assert info.get('winner') == 'X', f"Expected winner X, got {info.get('winner')}"
