from tictactoe_env import TicTacToeEnv, get_valid_moves

def test_reset_signature_and_constants():
    """Test that reset creates correct initial state using declared constants."""
    import numpy as np
    from tictactoe_env import BOARD_SIZE, EMPTY_CELL, PLAYER_X, PLAYER_O, TicTacToeEnv
    env = TicTacToeEnv()
    assert BOARD_SIZE == 9, 'BOARD_SIZE must be 9'
    assert EMPTY_CELL == 0, 'EMPTY_CELL must be 0'
    assert PLAYER_X == 1, 'PLAYER_X must be 1'
    assert PLAYER_O == -1, 'PLAYER_O must be -1'
    result = env.reset()
    assert isinstance(result, dict), 'reset() must return a dictionary'
    obs = result['board']
    info = result
    assert isinstance(obs, np.ndarray), 'obs must be numpy ndarray'
    assert obs.shape == (9,), 'obs shape must be (9,)'
    assert obs.dtype == np.int32, 'obs dtype must be int32'
    assert all(obs == 0), 'initial board must be all zeros'
    assert env.current_player == 1, 'current player must start as PLAYER_X'
    assert isinstance(env.history, list), 'history must be a list'
    assert len(env.history) == 0, 'initial history must be empty'
    assert env.terminal_state is False, 'initial state must not be terminal'
    assert env.winner is None, 'initial winner must be None'
    assert env.draw is False, 'initial draw flag must be False'

def test_step_invalid_action():
    """Test that step with invalid action returns 0 reward and sets info.valid_move=False."""
    from tictactoe_env import TicTacToeEnv
    env = TicTacToeEnv()
    env.reset()
    action_out_of_bounds = 10
    obs, reward, terminated, truncated, info = env.step(action_out_of_bounds)
    assert reward == 0, 'Reward for invalid move must be 0'
    assert terminated is False, 'Game must not terminate on invalid move'
    assert truncated is False, 'Truncated must be False'
    assert info.get('valid_move') is False, 'info.valid_move must be False for invalid action'

def test_step_valid_action():
    """Test that step with valid action updates state and switches player."""
    from tictactoe_env import TicTacToeEnv, get_valid_moves
    env = TicTacToeEnv()
    result = env.reset()
    obs_before = result['board']
    action = 0
    obs_after, reward, terminated, truncated, info = env.step(action)
    assert reward == 0, 'Reward for non-terminal move must be 0'
    assert terminated is False, 'Game should not end after first move'
    assert obs_after[0] != 0, 'Board at index 0 must be updated'
    assert env.current_player == -1, 'Current player should switch to PLAYER_O'
    valid_moves = get_valid_moves(env)
    assert 0 not in valid_moves, 'Index 0 (occupied) should not be in valid moves'
    assert len(valid_moves) == 8, 'Should have 8 remaining empty cells'

def test_step_invalid_action_info_structure():
    """Test that step provides correct info structure for invalid moves."""
    from tictactoe_env import TicTacToeEnv
    env = TicTacToeEnv()
    env.reset()
    action = 20
    _, _, _, _, info = env.step(action)
    assert 'valid_move' in info, "info dict must contain 'valid_move' key"
    assert info['valid_move'] is False, 'valid_move flag should be False for out-of-bounds actions'
    assert 'game_over' in info, "info dict must contain 'game_over' key"
    assert info['game_over'] is False, 'game_over flag should be False for out-of-bounds actions'
