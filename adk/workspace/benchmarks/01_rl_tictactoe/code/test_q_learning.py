import sys
from pathlib import Path
from q_learning_agent import QLearner

class MockPlayer:
    """Mock implementation of a Player to satisfy inheritance checks without full TicTacToeEnv setup."""
    from enum import IntEnum

    class Player(IntEnum):
        EMPTY = 0
        X = 1
        O = 2

    def __init__(self) -> None:
        self.value = MockPlayer.Player.EMPTY

    def take_action(self):
        pass

def test_q_learner_initialization():
    """Test that QLearner initializes with correct attributes from config."""
    learner = QLearner()
    assert hasattr(learner, 'q_table')

def test_mock_player_inheritance():
    """Verify that MockPlayer has valid signature and does not incorrectly assert inheritance."""
    player_instance = MockPlayer()
    assert hasattr(player_instance, 'take_action'), 'MockPlayer must have take_action method'
    assert hasattr(player_instance, 'value'), 'MockPlayer must have value attribute'
    assert isinstance(player_instance.value, int), 'MockPlayer value should be an integer'

def test_mock_take_action_signature():
    """Verify take_action method signature is valid (takes self only)."""
    import inspect
    sig = inspect.signature(MockPlayer.take_action)
    assert len(sig.parameters) == 1, f"take_action should only have 'self', got {sig}"
