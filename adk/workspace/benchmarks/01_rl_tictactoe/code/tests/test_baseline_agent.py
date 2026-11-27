from typing import List
import random

import pytest

from baseline_agent import RandomAgent


class TestRandomAgentInit:
    """Tests for RandomAgent initialization."""

    def test_init_no_seed(self) -> None:
        """Test that RandomAgent can be initialized without a seed (None)."""
        agent = RandomAgent(seed=None)
        # Check that the agent is created and has the required public method
        assert hasattr(agent, 'choose_action')

    def test_init_with_seed(self) -> None:
        """Test that RandomAgent initializes with a specific seed."""
        seed_val = 42
        agent = RandomAgent(seed=seed_val)
        # Check that the agent is created and has the required public method
        assert hasattr(agent, 'choose_action')

    def test_init_with_none_seed_explicit(self) -> None:
        """Test that providing seed=None is valid."""
        agent = RandomAgent(seed=None)
        # Check that the agent is created and has the required public method
        assert hasattr(agent, 'choose_action')


class TestRandomAgentChooseAction:
    """Tests for RandomAgent.choose_action method."""

    def test_choose_action_returns_valid_move(self) -> None:
        """Test that choose_action returns a value present in possible_moves."""
        agent = RandomAgent(seed=42)
        possible_moves = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        state_hash = 12345

        action = agent.choose_action(state_hash, possible_moves)
        assert action in possible_moves

    def test_choose_action_single_move(self) -> None:
        """Test behavior when only one move is possible."""
        agent = RandomAgent(seed=42)
        possible_moves = [4]
        state_hash = 12345

        action = agent.choose_action(state_hash, possible_moves)
        assert action == 4

    def test_choose_action_empty_list_raises_value_error(self) -> None:
        """Test that choose_action raises ValueError for empty possible_moves."""
        agent = RandomAgent(seed=42)
        state_hash = 12345

        with pytest.raises(ValueError):
            agent.choose_action(state_hash, [])

    def test_choose_action_deterministic_with_seed(self) -> None:
        """Test that choose_action produces reproducible results with a seed."""
        seed_val = 100
        possible_moves = [0, 3, 6] # Corners
        state_hash = 9999

        agent1 = RandomAgent(seed=seed_val)
        agent2 = RandomAgent(seed=seed_val)

        actions1 = [agent1.choose_action(state_hash + i, possible_moves) for i in range(10)]
        actions2 = [agent2.choose_action(state_hash + i, possible_moves) for i in range(10)]

        assert actions1 == actions2

    def test_choose_action_deterministic_different_seeds(self) -> None:
        """Test that different seeds produce different sequences (statistically unlikely to be same)."""
        seed_val1 = 100
        seed_val2 = 200
        possible_moves = [0, 3, 6]
        state_hash = 9999

        agent1 = RandomAgent(seed=seed_val1)
        agent2 = RandomAgent(seed=seed_val2)

        actions1 = [agent1.choose_action(state_hash + i, possible_moves) for i in range(10)]
        actions2 = [agent2.choose_action(state_hash + i, possible_moves) for i in range(10)]

        # While theoretically possible to match, it is extremely unlikely.
        assert actions1 != actions2

    def test_choose_action_does_not_modify_possible_moves(self) -> None:
        """Test that choose_action does not mutate the input list."""
        agent = RandomAgent(seed=42)
        possible_moves = [1, 2, 3]
        original_moves = list(possible_moves) # Copy of values

        _ = agent.choose_action(0, possible_moves)
        assert possible_moves == original_moves

    def test_choose_action_type_return(self) -> None:
        """Test that choose_action returns an int."""
        agent = RandomAgent(seed=42)
        possible_moves = [1, 2, 3]

        action = agent.choose_action(0, possible_moves)
        assert isinstance(action, int)

    def test_choose_action_with_various_lengths(self) -> None:
        """Test choose_action with different list lengths."""
        agent = RandomAgent(seed=42)

        # Length 1
        moves1 = [5]
        assert agent.choose_action(0, moves1) == 5

        # Length 2
        moves2 = [0, 8]
        action2 = agent.choose_action(1, moves2)
        assert action2 in moves2

        # Length 9 (full board)
        moves9 = list(range(9))
        action9 = agent.choose_action(2, moves9)
        assert action9 in moves9