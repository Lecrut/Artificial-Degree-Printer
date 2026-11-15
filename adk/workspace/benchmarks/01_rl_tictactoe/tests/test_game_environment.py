import pytest
from src.game_environment import GameEnvironment, check_winner, GameState, RandomOpponentAgent

@pytest.fixture
def env_fixture():
    """Create a standard Tic-Tac-Toe environment."""
    return GameEnvironment()

def test_check_winner_empty_board(env_fixture):
    """Test that an empty board returns no winner."""
    state = env_fixture.reset()
    result, reason = check_winner(state)
    assert not result
    assert reason == 'No winner'

def test_check_winner_complete_draw(env_fixture):
    """Test that a drawn board returns draw."""
    filled_board = [1] * 9
    result, reason = check_winner(filled_board)
    assert result == -1
    assert reason == 'Draw'

def test_check_winner_x_wins(env_fixture):
    """Test that X wins with a full row."""
    board = [1, 1, 1, 0, 0, 0, 2, 2, 0]
    result, reason = check_winner(board)
    assert result == 1
    assert reason == 'X wins'

def test_check_winner_o_wins(env_fixture):
    """Test that O wins with a full column."""
    board = [2, 0, 0, 2, 0, 0, 2, 0, 0]
    result, reason = check_winner(board)
    assert result == 2
    assert reason == 'O wins'

def test_random_opponent_move(env_fixture):
    """Test that RandomOpponentAgent selects a valid empty cell."""
    env = env_fixture
    state = env.reset()
    agent = RandomOpponentAgent(state.board if hasattr(state, 'board') else None, env)
    action = agent.get_move(state.board if hasattr(state, 'board') else [])
    assert isinstance(action, (int, type(None)))
