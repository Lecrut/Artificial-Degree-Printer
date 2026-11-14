import pytest
from tictactoe_env import TicTacToeEnv, Player

def test_initial_state_is_empty():
    """Test that a new game starts empty."""
    env = TicTacToeEnv()
    env.reset()
    assert env.get_winner() is None, 'Expected winner to be None initially'
    assert not env.is_game_over(), 'Expected game NOT to be over initially'

def test_terminal_states_correct_winner_detection():
    """Test winner detection for various terminal states."""
    import tictactoe_env
    player_x = None
    player_o = None
    for attr in dir(tictactoe_env):
        val = getattr(tictactoe_env, attr)
        if isinstance(val, int) or (hasattr(val, 'value') and isinstance(val.value, int)):
            if attr in ('X', 'O', 1, -1):
                if attr == 'X' or val == 1 or (hasattr(val, 'value') and val.value == 1):
                    player_x = val
                elif attr == 'O' or val == -1 or (hasattr(val, 'value') and val.value == -1):
                    player_o = val
            if player_x is None:
                player_x = val
                continue
            if player_o is None and val not in (player_x,) if hasattr(player_x, 'value') else (player_x.value,):
                player_o = val
    try:
        x_player = Player.X
    except AttributeError:
        x_player = getattr(Player, 'X', None) or 1
    try:
        pass
    except AttributeError:
        getattr(Player, 'O', None) or -1
    env_x = TicTacToeEnv()
    env_x.reset()
    for i in range(3):
        env_x._state[i] = x_player if isinstance(x_player, int) else x_player.value
        env_x._state[i + 3] = x_player if isinstance(x_player, int) else x_player.value
        env_x._state[i + 6] = x_player if isinstance(x_player, int) else x_player.value
    winner_x = env_x.get_winner()
    assert winner_x == x_player or winner_x.value == x_player if hasattr(x_player, 'value') else winner_x == x_player
