"""
Uniform random agent (baseline) implementation.
Selects an available empty cell uniformly at random.
"""
import numpy as np
from typing import List, Tuple

class RandomAgent:
    """A baseline agent that selects moves purely at random.
    
    This class implements a uniform random mover suitable for use as
    a performance baseline in reinforcement learning experiments against
    other agents (e.g., Q-Learning). It does not store memory or learn
    from the environment.
    """

    def __init__(self) -> None:
        """Initialize a uniform random mover."""
        # No initialization required for this agent as it has no internal state.
        pass

    def choose_action(self, available_actions: List[int]) -> int:
        """Select an action uniformly at random from the provided list.
        
        This method is used to execute a single move during training or
evaluation when the agent is instructed which valid moves are possible.

        Args:
            available_actions: A list of integers representing the indices
                of valid moves (empty cells) for the current game state.

        Returns:
            The index of the chosen action as an integer.

        Raises:
            ValueError: If the list of available actions is empty,
                meaning no legal move exists in the given state.
        """
        if len(available_actions) == 0:
            raise ValueError("No available actions found for the current state.")
        
        return int(np.random.choice(available_actions))