import pytest
from tictactoe_env import TicTacToeEnv, Player

def test_initial_state_is_empty():
    """Test that a new game starts empty."""
    env = TicTacToeEnv()
    env.reset()
    # Check for None directly, avoiding potential attribute errors on the enum class itself
    assert env.get_winner() is None, 'Expected winner to be None initially'
    assert not env.is_game_over(), 'Expected game NOT to be over initially'

def test_terminal_states_correct_winner_detection():
    """Test winner detection for various terminal states."""
    # Explicitly use known enum members if they exist, otherwise fall back to standard convention
    # Based on error logs, we expect PLAYER_ONE and AI. We will try to access them by name.
    player_one = getattr(Player, 'PLAYER_ONE', None)
    player_ai = getattr(Player, 'AI', None)
    
    assert player_one is not None and player_ai is not None, f"Could not identify PLAYER_ONE or AI in Player enum: {dir(Player)}"
    
    # Create state for PLAYER_ONE
    env_x = TicTacToeEnv()
    env_x.reset()
    p1_val = player_one.value if hasattr(player_one, 'value') else player_one
    # Fill entire board with Player 1 to force a win
    for i in range(9):
        env_x._state[i] = p1_val
    
    assert env_x.get_winner() == player_one, f'Expected winner {player_one}, got {env_x.get_winner()}'
    
    # Create state for AI
    env_ai = TicTacToeEnv()
    env_ai.reset()
    ai_val = player_ai.value if hasattr(player_ai, 'value') else player_ai
    # Fill entire board with Player AI to force a win
    for i in range(9):
        env_ai._state[i] = ai_val
    
    assert env_ai.get_winner() == player_ai, f'Expected winner {player_ai}, got {env_ai.get_winner()}'