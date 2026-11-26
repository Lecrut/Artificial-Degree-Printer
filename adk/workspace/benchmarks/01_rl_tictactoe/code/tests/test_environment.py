import gymnasium as gym
import numpy as np
from environment import TicTacToeEnv

def test_tic_tac_toe_env_init():
    """Test initialization of TicTacToeEnv creates valid spaces and initial board."""
    env = TicTacToeEnv()
    assert isinstance(env.observation_space, gym.spaces.Box)
    assert env.observation_space.shape == (3, 3)
    assert isinstance(env.action_space, gym.spaces.Discrete)
    assert env.action_space.n == 9
    obs, info = env.reset()
    if obs.shape == (3, 3):
        assert np.array_equal(obs, np.zeros((3, 3)))
    else:
        assert obs.shape == (9,)
        assert np.array_equal(obs, np.zeros(9))
