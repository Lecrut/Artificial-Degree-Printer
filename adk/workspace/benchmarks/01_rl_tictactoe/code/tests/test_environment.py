import numpy as np
import pytest
from environment import TicTacToeEnv


def test_reset_initial_state():
    """Test that reset returns an all -1 board."""
    env = TicTacToeEnv()
    obs, info = env.reset()
    assert (obs == -1).all()


def test_step_valid_observations_and_rewards():
    """Test that step returns correct observation shape and reward type."""
    env = TicTacToeEnv()
    _ = env.reset()
    obs, reward, term, trunc, info = env.step(4)
    assert isinstance(obs, np.ndarray)
    assert obs.shape == (3, 3)
    assert term is False


def test_get_legal_moves_count():
    """Test that get_legal_moves returns 9 moves on an empty board."""
    env = TicTacToeEnv()
    _ = env.reset()
    moves = env.get_legal_moves(-1)
    assert len(moves) == 9