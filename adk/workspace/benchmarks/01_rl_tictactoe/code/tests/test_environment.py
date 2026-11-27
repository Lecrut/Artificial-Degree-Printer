import pytest
import numpy as np
from typing import Dict, Any
import gymnasium as gym
from environment import TicTacToeEnv, BOARD_SIZE, NUM_ACTIONS, PLAYER_X, PLAYER_O, DRAW_REWARD, WIN_REWARD, LOSS_REWARD
from gymnasium import spaces

class TestConstants:
    """Test module-level constants defined in environment.py."""

    def test_board_size(self):
        assert BOARD_SIZE == 3

    def test_num_actions(self):
        assert NUM_ACTIONS == 9

    def test_player_x(self):
        assert PLAYER_X == 1

    def test_player_o(self):
        assert PLAYER_O == -1

    def test_rewards(self):
        assert DRAW_REWARD == 0.5
        assert WIN_REWARD == 1.0
        assert LOSS_REWARD == -1.0

class TestTicTacToeEnvInitialization:
    """Test the initialization of TicTacToeEnv."""

    def test_spaces_are_discrete(self):
        env = TicTacToeEnv()
        assert isinstance(env.observation_space, spaces.Discrete)
        assert isinstance(env.action_space, spaces.Discrete)

    def test_observation_space_size(self):
        """Observation space should cover all possible board states.
        3^9 = 19683. The hash is derived from interpreting the 3x3 board as a base-3 number.
        """
        env = TicTacToeEnv()
        assert env.observation_space.n == 3 ** BOARD_SIZE ** 2

    def test_action_space_size(self):
        env = TicTacToeEnv()
        assert env.action_space.n == NUM_ACTIONS

class TestTicTacToeEnvReset:
    """Test the reset method of TicTacToeEnv."""

    def test_reset_returns_tuple_of_length_2(self):
        env = TicTacToeEnv()
        obs, info = env.reset(seed=42)
        assert isinstance(obs, int)
        assert isinstance(info, dict)
        assert len((obs, info)) == 2

    def test_reset_initial_state_is_empty(self):
        env = TicTacToeEnv()
        obs, _ = env.reset(seed=123)
        assert obs == 0

    def test_reset_info_is_empty_dict(self):
        env = TicTacToeEnv()
        _, info = env.reset(seed=456)
        assert info == {}

    def test_reset_deterministic_with_seed(self):
        env1 = TicTacToeEnv()
        obs1, _ = env1.reset(seed=999)
        env2 = TicTacToeEnv()
        obs2, _ = env2.reset(seed=999)
        assert obs1 == obs2

class TestTicTacToeEnvStep:
    """Test the step method of TicTacToeEnv."""

    def test_step_valid_move_updates_state(self):
        """Verify that a valid move by X updates the observation from 0 and does not terminate."""
        env = TicTacToeEnv()
        obs, _ = env.reset(seed=1)
        assert obs == 0
        new_obs, reward, terminated, truncated, info = env.step(4)
        assert new_obs != 0, 'Valid move should change the board state hash'
        assert terminated is False
        assert truncated is False
        assert reward == 0.0
        assert info['valid_move'] is True

    def test_step_invalid_move_does_not_update_state(self):
        """Verify that an invalid move returns the same observation and marks the move as invalid."""
        env = TicTacToeEnv()
        obs, _ = env.reset(seed=1)
        original_obs = obs
        new_obs, reward, terminated, truncated, info = env.step(9)
        assert new_obs == original_obs
        assert info['valid_move'] is False
        assert terminated is False
        assert reward == 0.0

    def test_step_win_for_x(self):
        """Test a scenario where X wins."""
        env = TicTacToeEnv()
        obs, _ = env.reset(seed=42)
        _, _, term1, _, info1 = env.step(0)
        assert not term1
        _, _, term2, _, info2 = env.step(4)
        assert not term2
        new_obs, reward, terminated, truncated, info = env.step(8)
        assert terminated is True
        assert info['winner'] == PLAYER_X
        assert reward == WIN_REWARD
        assert truncated is False

    def test_step_invalid_move_returns_info(self):
        env = TicTacToeEnv()
        obs, _ = env.reset(seed=1)
        new_obs, reward, terminated, truncated, info = env.step(9)
        assert info['valid_move'] is False
        assert new_obs == obs
        assert reward == 0.0

    def test_step_valid_move_returns_info(self):
        env = TicTacToeEnv()
        obs, _ = env.reset(seed=1)
        new_obs, reward, terminated, truncated, info = env.step(0)
        assert info['valid_move'] is True
        assert info['winner'] is None
        assert new_obs != obs

class TestGetStateHash:
    """Test get_state_hash method."""

    def test_empty_board_hash_is_zero(self):
        env = TicTacToeEnv()
        empty_board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)
        assert env.get_state_hash(empty_board) == 0

    def test_unique_hashes_for_different_states(self):
        env = TicTacToeEnv()
        board1 = np.zeros((3, 3), dtype=int)
        board2 = np.zeros((3, 3), dtype=int)
        board2[0, 0] = 1
        hash1 = env.get_state_hash(board1)
        hash2 = env.get_state_hash(board2)
        assert hash1 != hash2

    def test_max_hash_is_correct(self):
        """Full board with all X (1) should be max value in base 3 representation.
        Full board with 1s corresponds to digits all being 1. 
        Value = sum(1 * 3^i for i in range(9)) = (3^9 - 1) / (3 - 1) = 19682 / 2 = 9841.
        """
        env = TicTacToeEnv()
        full_board = np.ones((3, 3), dtype=int)
        expected_max = (3 ** BOARD_SIZE ** 2 - 1) // 2
        assert env.get_state_hash(full_board) == expected_max

    def test_get_valid_moves_returns_list_of_ints(self):
        """Test that get_valid_moves returns a list of integers."""
        env = TicTacToeEnv()
        obs, _ = env.reset(seed=1)
        valid_moves = env.get_valid_moves()
        assert isinstance(valid_moves, list)
        assert all((isinstance(m, int) for m in valid_moves))
        assert len(valid_moves) == 9

    def test_get_valid_moves_after_moves(self):
        """Test that get_valid_moves updates after moves are made."""
        env = TicTacToeEnv()
        obs, _ = env.reset(seed=1)
        valid_moves_before = set(env.get_valid_moves())
        assert len(valid_moves_before) == 9
        _, _, _, _, _ = env.step(0)
        valid_moves_after = set(env.get_valid_moves())
        assert len(valid_moves_after) == 8
        assert 0 not in valid_moves_after
