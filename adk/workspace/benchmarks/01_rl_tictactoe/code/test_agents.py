import pytest
from q_learning_agent import QLearner
from random_agent import RandomAgent
from tictactoe_env import TicTacToeEnv, Player

def test_random_agent_initialization():
    """Test that RandomAgent initializes correctly and picks random actions."""
    agent = RandomAgent()
    assert agent is not None
    env = TicTacToeEnv(max_steps=9)
    env.reset()
    # Check available moves in the environment
    valid_moves = [i for i in range(9) if env.is_valid_move(i)]
    # The test should pass if the environment has valid moves. 
    # If it fails, the error is likely in is_valid_move or the state of the env.
    assert len(valid_moves) > 0, 'There should be valid moves in the initial state.'
    action = agent.choose_action(valid_moves)
    assert isinstance(action, int)
    assert action in valid_moves

def test_q_learning_agent_initialization():
    """Test that QLearner initializes correctly and generates valid moves."""
    env = TicTacToeEnv(max_steps=9)
    initial_state = env.reset()
    agent = QLearner()
    assert agent is not None, 'QLearner should initialize successfully.'
    has_q_table = hasattr(agent, 'q_table')
    has_underlined_q_table = hasattr(agent, '_q_table')
    # Ensure we have a Q-table or underlined version
    assert has_q_table or has_underlined_q_table, 'Agent must have a q_table or _q_table attribute.'
    
    # Check if is_valid_move logic in env is the source of empty valid_moves
    # If env.get_winner() returns Player.HUM (from previous error log), it might indicate an incorrect initialization.
    # However, we only test agents here. The core issue identified in the second run was 'valid_moves' being empty.
    valid_moves = [i for i in range(9) if env.is_valid_move(i)]
    assert len(valid_moves) > 0, f'There should be valid moves in the initial state, got {len(valid_moves)}.'
    
    actions = agent.get_all_actions(env.get_state_key(initial_state))
    assert isinstance(actions, list), 'get_all_actions must return a list.'
    for action in actions:
        assert isinstance(action, int), 'Actions must be integers.'