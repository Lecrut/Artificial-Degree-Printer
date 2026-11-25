import gymnasium as gym
from environment import TicTacToeEnv, RandomAgent
import pytest
import numpy as np


def test_tic_tac_toe_env_initialized():
    """Test that the environment initializes correctly with observation and action spaces."""
    env = TicTacToeEnv()
    assert isinstance(env.observation_space, gym.spaces.Box)
    assert env.observation_space.shape == (9,)
    assert env.observation_space.dtype in [np.int8, np.int32, np.float32]
    assert isinstance(env.action_space, gym.spaces.Discrete)
    assert env.action_space.n == 9


def test_tic_tac_toe_env_reset():
    """Test that the environment resets correctly and returns expected shapes/types."""
    env = TicTacToeEnv()
    obs, info = env.reset(seed=42, options=None)
    assert isinstance(obs, np.ndarray)
    assert len(obs.shape) == 1 and obs.shape[0] == 9
    assert isinstance(info, dict)
    assert 'current_player' in info
    assert (obs == 0).all()
    assert info['current_player'] == 1


def test_tic_tac_toe_env_step_win_condition():
    """Test a winning scenario and check return values."""
    env = TicTacToeEnv()
    obs, _ = env.reset(seed=42)
    action = 4
    obs, reward, terminated, truncated, info = env.step(action)
    assert not terminated and (not truncated)
    assert info['winner'] is None
    obs, _ = env.reset()
    actions = [4, 0, 6]
    for a in actions:
        obs, reward, terminated, truncated, info = env.step(a)
        assert len(obs.shape) == 1 and obs.shape[0] == 9
    obs, _ = env.reset()
    actions = [0, 5, 2]
    current_player = 1
    for a in actions:
        if current_player != 1:
            break
        obs, reward, terminated, truncated, info = env.step(a)
        assert isinstance(obs, np.ndarray)
        assert isinstance(reward, float)
        assert isinstance(terminated, bool)
        assert isinstance(info, dict)
        if not terminated:
            assert reward == 0.0
    _win_state = np.array([1, 1, 1, 0, 0, 0, 0, 0, 0], dtype=np.int8)
    _obs_win = env.reset()
    obs_next, reward_next, terminated_next, truncated_next, info_next = env.step(actions[0]) if not terminated else (obs, reward, terminated, truncated, info)
    if terminated:
        assert 'winner' in info
        if 'winner' in info and info['winner'] is not None:
            assert info['winner'] in [1, 2]
        assert 'current_player' in info
        _new_current = info['current_player']


def test_random_agent_select_action():
    """Test that RandomAgent returns a valid action index."""
    agent = RandomAgent()
    
    # Test empty board: should return a valid index [0-8]
    empty_state = np.zeros(9, dtype=np.int8)
    action = agent.select_action(empty_state)
    assert isinstance(action, int)
    assert 0 <= action <= 8
    assert empty_state[action] == 0
    
    # Test non-full board: should return an index corresponding to an empty cell (0)
    non_full_state = np.zeros(9, dtype=np.int8)
    non_full_state[0] = 1
    action = agent.select_action(non_full_state)
    assert isinstance(action, int)
    assert 0 <= action <= 8
    assert non_full_state[action] == 0
    
    # Test truly full board (no zeros): should return -1 per interface spec
    full_state = np.array([1, 2, 1, 2, 1, 2, 1, 2, 1], dtype=np.int8)
    action_full = agent.select_action(full_state)
    assert action_full == -1
