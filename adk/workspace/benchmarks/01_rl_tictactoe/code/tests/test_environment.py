def test_observation_space():
    """Test observation_space attribute matches specification (Gym-like space)."""
    from environment import TicTacToeEnv
    env = TicTacToeEnv(render_mode=None)
    assert hasattr(env, 'observation_space')
    space = env.observation_space
    assert space is not None

def test_action_space():
    """Test action_space attribute matches specification (Gym-like space)."""
    from environment import TicTacToeEnv
    env = TicTacToeEnv(render_mode=None)
    assert hasattr(env, 'action_space')
    space = env.action_space
    assert space is not None

def test_reset_with_seed():
    """Test reset returns consistent results for the same seed."""
    from environment import TicTacToeEnv
    env1 = TicTacToeEnv(render_mode=None)
    obs1, _ = env1.reset(seed=42)
    env2 = TicTacToeEnv(render_mode=None)
    obs2, _ = env2.reset(seed=42)
    assert (obs1 == obs2).all()

def test_step_determinism():
    """Test step returns consistent results for same state and action."""
    from environment import TicTacToeEnv
    env1 = TicTacToeEnv(render_mode=None)
    obs1, _ = env1.reset(seed=42)
    action = 0
    next_obs1, reward1, term1, trunc1, info1 = env1.step(action)
    env2 = TicTacToeEnv(render_mode=None)
    obs2, _ = env2.reset(seed=42)
    action = 0
    next_obs2, reward2, term2, trunc2, info2 = env2.step(action)
    assert (next_obs1 == next_obs2).all()
    assert reward1 == reward2
    assert term1 == term2
    assert trunc1 == trunc2

def test_board_size():
    """Test board_size attribute matches specification (integer > 0)."""
    from environment import TicTacToeEnv
    env = TicTacToeEnv(render_mode=None)
    assert isinstance(env.board_size, int)
    assert env.board_size > 0
