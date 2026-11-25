def test_play_game_interface_and_contract():
    """
    Tests the contract of `play_game`:
    1. Accepts exact arguments defined in interface.
    2. Returns a dictionary with expected keys and types.
    3. Handles deterministic logic based on provided RNG seed.
    """
    import pytest
    from game_loop import play_game
    from tictactoe_env import PLAYER_X, PLAYER_O
    import numpy as np

    def agent_a_state_only(board):
        return 0

    def agent_b_state_and_rng(state, rng):
        idx = rng.integers(0, 9)
        if idx > 8:
            idx = 0
        return idx
    assert PLAYER_X == 1, 'PLAYER_X must be 1.'
    assert PLAYER_O == -1, 'PLAYER_O must be -1.'
    rng = np.random.default_rng(42)
    result = play_game(agent_a_state_only, agent_b_state_and_rng, is_agent_a_turn=True, rng=rng)
    assert isinstance(result, dict), 'Return type must be a dictionary.'
    required_keys = ['winner', 'moves', 'final_board', 'total_turns', 'rewards_A', 'rewards_B']
    for key in required_keys:
        assert key in result, f"Missing key '{key}' in return dictionary."
    assert isinstance(result['winner'], str), "Winner must be a string ('A', 'B', or 'draw')."
    assert isinstance(result['moves'], list), 'Moves must be a list.'
    assert isinstance(result['final_board'], np.ndarray), 'Final board must be a numpy array.'
    assert isinstance(result['total_turns'], int), 'Total turns must be an integer.'
    assert isinstance(result['rewards_A'], (int, float)), 'Rewards_A must be a number.'
    assert isinstance(result['rewards_B'], (int, float)), 'Rewards_B must be a number.'
    for move in result['moves']:
        assert isinstance(move, dict), 'Each move must be a dictionary.'
        assert 'player' in move, "Each move must contain 'player'."
        assert 'action' in move, "Each move must contain 'action'."
        assert isinstance(move['player'], str), "Player key must be a string ('A' or 'B')."
        assert isinstance(move['action'], int), 'Action key must be an integer.'
    assert len(result['moves']) == result['total_turns'], 'Number of moves must equal total_turns.'
    assert result['final_board'].shape == (3, 3), f"Final board shape must be (3,3), got {result['final_board'].shape}."
