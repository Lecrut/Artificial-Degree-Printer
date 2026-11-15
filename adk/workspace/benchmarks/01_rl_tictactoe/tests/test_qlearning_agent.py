import pytest
from typing import Callable
from unittest.mock import Mock
import sys
sys.path.insert(0, 'src')
from config import Config
from qlearning_agent import QLearningAgent

@pytest.fixture
def agent_factory() -> Callable[[Config], QLearningAgent]:
    """Fixture that returns a factory function to create initialized QLearningAgent instances."""
    def _factory(config: Config) -> QLearningAgent:
        return QLearningAgent(config)
    return _factory

def test_qupdate_table_update(agent_factory: Callable[[Config], QLearningAgent]) -> None:
    """Test Q-Table update logic via mock interface."""
    pass