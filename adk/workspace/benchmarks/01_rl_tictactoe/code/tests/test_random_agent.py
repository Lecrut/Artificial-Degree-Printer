import pytest
from random_agent import RandomAgent
import numpy as np


def test_act_returns_valid_move_for_non_terminal() -> None:
    """Test that act returns an integer index of a valid empty cell for non-terminal states."""
    agent = RandomAgent()
    rng = np.random.default_rng(42)

    # Construct a state with exactly one valid empty move (index 3)
    state_with_moves: dict[int, str | None] = {
        0: "O",
        1: "O",
        2: "O",
        3: None,
        4: "X",
        5: "X",
        6: None,
        7: None,
        8: None
    }

    action = agent.act(state_with_moves, rng)

    # Specification check: act() must return an integer index when valid moves exist.
    assert isinstance(action, int), f"act() must return an integer index, got {type(action)}"
    
    # Specification check: Return value must be a valid cell identifier (0-8) found in state keys.
    assert action in state_with_moves, f"Action {action} is not a valid key in the state dictionary."


def test_act_returns_minus_one_for_terminal() -> None:
    """Test that act returns -1 when no valid moves exist (terminal state)."""
    agent = RandomAgent()
    rng = np.random.default_rng(42)

    # Construct a terminal state with no empty cells.
    full_state_dict: dict[int, str] = {
        0: "O",
        1: "O",
        2: "O",
        3: "X",
        4: "X",
        5: "X",
        6: "X",
        7: "O",
        8: "X"
    }

    action_terminal = agent.act(full_state_dict, rng)
    assert action_terminal == -1, "act() must return -1 when no valid moves exist."


def test_act_returns_random_index_from_available_moves() -> None:
    """Test that act selects uniformly at random from available empty cells."""
    agent = RandomAgent()
    rng = np.random.default_rng(0)

    # Create a state where 4 moves are available: indices 1, 2, 5, 6
    state_with_moves: dict[int, str | None] = {
        0: "X",
        1: None,
        2: None,
        3: "O",
        4: "O",
        5: None,
        6: None,
        7: "X",
        8: "X"
    }

    valid_moves = [1, 2, 5, 6]
    results = []
    for _ in range(100):
        action = agent.act(state_with_moves, rng)
        assert isinstance(action, int)
        assert action in valid_moves, f"Action {action} is not one of the valid moves {valid_moves}"
        results.append(action)

    # Basic statistical check: ensure all valid moves were selected at least once over many iterations.
    # Note: This is probabilistic but highly likely to pass with 100 samples and 4 options.
    assert len(set(results)) == 4, "Not all valid moves were selected in the sample; agent may not be truly random."
