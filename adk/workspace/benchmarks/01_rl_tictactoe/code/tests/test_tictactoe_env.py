import numpy as np
import pytest
from environment.tictactoe_env import TicTacToeEnv, BOARD_SIZE, WINNING_LINES

def test_reset_shape():
    """Assert `obs.shape == (9,)` and all zeros."""
    env = TicTacToeEnv()
    obs, _ = env.reset(seed=42)
    assert obs.shape == (BOARD_SIZE,), f'Expected shape {(BOARD_SIZE,)}, got {obs.shape}'
    assert np.all(obs == 0), 'Board should be all zeros after reset'

def test_get_valid_actions_count():
    """Assert `len(env.get_valid_actions()) == 9` after reset."""
    env = TicTacToeEnv()
    obs, _ = env.reset(seed=42)
    valid_actions = env.get_valid_actions()
    assert len(valid_actions) == BOARD_SIZE, f'Expected {BOARD_SIZE} valid actions, got {len(valid_actions)}'

def test_step_updates_board():
    """Call `env.step(0)`, assert the board state changes."""
    env = TicTacToeEnv()
    obs, _ = env.reset(seed=42)
    initial_obs = obs.copy()
    new_obs, _, terminated, truncated, info = env.step(0)
    assert new_obs[0] != 0, 'Expected board to change at index 0 after step(0)'
    expected_board = initial_obs.copy()
    expected_board[0] = 1
    assert np.array_equal(new_obs, expected_board), 'Full board state mismatch after step'

def test_step_invalid_action():
    """Assert `ValueError` is raised when stepping on an occupied cell."""
    env = TicTacToeEnv()
    obs, _ = env.reset(seed=42)
    env.step(0)
    with pytest.raises(ValueError):
        env.step(0)

def test_win_horizontal():
    """Simulate a horizontal win for Player X (indices 0, 1, 2).
    
    Since the environment alternates players automatically:
    - Reset.
    - X plays 0. Opponent plays *anywhere safe* (e.g., 4) by calling step(4). 
    - X plays 1. Opponent plays *anywhere safe* (e.g., 5) by calling step(5).
    - X plays 2. Check `terminated=True` and `reward=1.0`.
    """
    env = TicTacToeEnv()
    obs, _ = env.reset(seed=42)
    obs, _, terminated, truncated, info = env.step(0)
    assert not terminated, 'Game should not terminate yet after first move'
    obs, _, terminated, truncated, info = env.step(5)
    assert not terminated, 'Game should not terminate yet after opponent move'
    obs, _, terminated, truncated, info = env.step(1)
    assert not terminated, 'Game should not terminate yet after second move by X'
    obs, _, terminated, truncated, info = env.step(8)
    assert not terminated, 'Game should not terminate yet after opponent second move'
    obs, reward, terminated, truncated, info = env.step(2)
    assert terminated, 'Game should be terminated on win'
    assert reward == 1.0, f'Reward should be +1 for winner, got {reward}'

def test_draw():
    """Simulate a full board fill without wins. Check `terminated` is True and `reward` is 0.

    Sequence: 4, 6, 1, 7, 2, 8, 0, 5, 3.
    X(4), O(6), X(1), O(7), X(2), O(8), X(0), O(5), X(3).
    Final Board:
     1 -1  0
    -1  1 -1
     0  1  1
    No wins. Full board.
    """
    env = TicTacToeEnv()
    obs, _ = env.reset(seed=42)
    seq = [4, 6, 1, 7, 2, 8, 0, 5, 3]
    for i, action in enumerate(seq):
        obs, reward, terminated, truncated, info = env.step(action)
        if i < len(seq) - 1:
            assert not terminated, f'Game terminated prematurely on move {i + 1} with action {action}'
    obs, reward, terminated, truncated, info = env.step(seq[-1])
    assert terminated, 'Game should be terminated on draw'
    assert reward == 0.0, f'Reward should be 0 for draw, got {reward}'

def test_spaces_metadata():
    """Assert `observation_space.shape == (9,)` and `action_space.n == 9`."""
    env = TicTacToeEnv()
    assert env.observation_space.shape == (BOARD_SIZE,), f'Observation space shape mismatch: {env.observation_space.shape}'
    assert env.action_space.n == BOARD_SIZE, f'Action space n mismatch: {env.action_space.n}'
