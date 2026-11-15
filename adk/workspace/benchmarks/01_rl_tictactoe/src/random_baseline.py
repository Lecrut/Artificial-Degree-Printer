"""Random Baseline Module.

Provides a baseline agent that plays Tic-Tac-Toe by selecting random valid moves, serving as a lower bound for performance metrics."""
from typing import TypeVar, Generic, Any
import numpy as np
from typing import TypeVar, Generic
import copy
from dataclasses import dataclass
TicTacToeEnv = 'src.tictactoe_env.TicTacToeEnv'
State = TypeVar('State')
QEntry = dataclass

class RandomBaseline(Generic[TypeVar('State')]):
    """Agent that plays randomly to establish a performance floor."""

    def __init__(self, rng: np.random.Generator) -> None:
        """Initialize the baseline agent with a random number generator.

        Args:
            rng: A numpy random generator for reproducible randomness.
        """
        self._rng = rng

    def play_episode(self, env: Any, agent_state: State) -> int:
        """Simulate one episode against the environment.

    Args:
        env: The TicTacToe environment instance.
        agent_state: The initial state of the game for the agent.

    Returns:
        1 if the agent wins, 0 if it loses or draws.
    """
        current_state = copy.deepcopy(agent_state)
        winner = None
        is_agent_turn = True
        while winner is None and len(env.get_available_moves(current_state)) > 0:
            if not is_agent_turn:
                pass
            else:
                available_moves = env.get_available_moves(current_state)
                if len(available_moves) == 0:
                    break
                move_idx = self._rng.choice(len(available_moves))
                next_state = env.apply_move(current_state, available_moves[move_idx])
                current_state = next_state
            winner = env.get_winner(current_state)
            if winner is not None:
                break
            is_agent_turn = not is_agent_turn
        if winner == 'A':
            return 1
        elif winner == 'B' or (len(env.get_available_moves(current_state)) == 0 and winner is None):
            return 0

    def get_action(self, state: State) -> int:
        """Returns a random valid move index.

    Args:
        self: The RandomBaseline agent instance.
        state: The current game state.

    Returns:
        A randomly selected action from the available options at `state`.
    """
        pass

def play_episode(self, env: Any, agent_state: State) -> int:
    """Simulate one episode against the environment.

    Args:
        env: The TicTacToe environment instance.
        agent_state: The initial state of the game for the agent.

    Returns:
        1 if the agent wins, 0 if it loses or draws.
    """
    import random
    current_state = copy.deepcopy(agent_state)
    winner = None
    is_agent_turn = True
    while winner is None and len(env.get_available_moves(current_state)) > 0:
        if not is_agent_turn:
            pass
        else:
            available_moves = env.get_available_moves(current_state)
            if len(available_moves) == 0:
                break
            move = random.choice(available_moves)
            next_state = env.apply_move(current_state, move)
            current_state = next_state
        winner = env.get_winner(current_state)
        if winner is not None:
            break
        is_agent_turn = not is_agent_turn
    if winner == 'A':
        return 1
    elif winner == 'B' or (len(env.get_available_moves(current_state)) == 0 and winner is None):
        return 0

def get_action(self, env: Any, state: State) -> int:
    """Returns a random valid move index.

    Args:
        self: The RandomBaseline agent instance.
        env: The environment to query for available moves.
        state: The current game state.

    Returns:
        A randomly selected action from the available options at `state`.
    """
    available_moves = env.get_available_moves(state)
    if not available_moves:
        return 0
    return self._rng.choice(available_moves)
