import pytest
import numpy as np
import environment


def test_constants_are_correct() -> None:
    """Test that declared constants match the specification exactly."""
    assert environment.BOARD_SIZE == 3
    assert environment.STATE_SPACE_SIZE == 19683
    assert environment.ACTION_SPACE_SIZE == 9
    assert environment.PLAYER_X == 1
    assert environment.PLAYER_O == -1
    assert environment.REWARD_WIN == 1.0
    assert environment.REWARD_DRAW == 0.0
    assert environment.REWARD_LOSS == -1.0


def test_env_reset_shape() -> None:
    """Test that reset returns the correct initial state shape and values."""
    env = environment.TicTacToeEnv()
    state = env.reset(seed=42)
    assert isinstance(state, np.ndarray)
    assert state.shape == (9,)
    assert np.all(state == 0)


def test_env_step_valid_move() -> None:
    """Test that a valid move updates the board correctly."""
    env = environment.TicTacToeEnv()
    obs = env.reset(seed=42)

    # Player X moves first to cell 0 (top-left)
    next_obs, reward, terminated, truncated, info = env.step(action=0)

    assert not terminated
    assert not truncated
    # The board should now have a 1 at index 0 and 0 elsewhere
    expected_board = np.zeros(9, dtype=int)
    expected_board[0] = environment.PLAYER_X
    assert np.array_equal(next_obs, expected_board)
    # Next player should be O
    assert info['player'] == environment.PLAYER_O
    # Action 0 should no longer be legal
    assert 0 not in info['legal_actions']
    # Reward is 0 because the game isn't over yet (and it's not a draw)
    assert reward == environment.REWARD_DRAW


def test_env_step_invalid_occupied_cell() -> None:
    """Test that stepping on an occupied cell raises ValueError."""
    env = environment.TicTacToeEnv()
    env.reset(seed=42)

    # First step makes cell 0 occupied
    env.step(action=0)

    # Second step on the same cell should raise ValueError
    with pytest.raises(ValueError):
        env.step(action=0)


def test_env_step_invalid_action_index() -> None:
    """Test that stepping with an invalid action index raises ValueError."""
    env = environment.TicTacToeEnv()
    env.reset(seed=42)

    with pytest.raises(ValueError):
        env.step(action=9)


def test_env_step_win_condition_x() -> None:
    """Test that the game terminates with a win for X when X gets 3 in a row."""
    env = environment.TicTacToeEnv()
    obs = env.reset(seed=42)

    # Simulate a quick win for X: 
    # Board indices:
    # 0 | 1 | 2
    # ---+---+---
    # 3 | 4 | 5
    # ---+---+---
    # 6 | 7 | 8

    # Move 1: X places at 0 (top-left)
    obs, _, term, _, info = env.step(0)
    assert not term
    assert info['player'] == environment.PLAYER_O

    # Move 2: O places at 1 (top-middle) - arbitrary move by opponent
    obs, _, term, _, info = env.step(1)
    assert not term
    assert info['player'] == environment.PLAYER_X

    # Move 3: X places at 3 (middle-left)
    obs, _, term, _, info = env.step(3)
    assert not term
    assert info['player'] == environment.PLAYER_O

    # Move 4: O places at 2 (top-right) - arbitrary move by opponent
    obs, _, term, _, info = env.step(2)
    assert not term
    assert info['player'] == environment.PLAYER_X

    # Move 5: X places at 6 (bottom-left) -> Wins column (0, 3, 6)
    obs, reward, term, _, _ = env.step(6)

    assert term
    assert reward == environment.REWARD_WIN


def test_env_step_draw_condition() -> None:
    """Test that the game terminates with a draw when board is full."""
    env = environment.TicTacToeEnv()
    obs = env.reset(seed=42)

    # Fill the board completely without any wins
    # X: 0, O: 1, X: 2, O: 3, X: 4, O: 5, X: 6, O: 7, X: 8
    moves = [0, 1, 2, 3, 4, 5, 6, 7, 8]
    last_reward = 0.0

    for move in moves:
        obs, reward, term, truncated, info = env.step(move)
        last_reward = reward
        if term:
            break

    assert term
    assert last_reward == environment.REWARD_DRAW