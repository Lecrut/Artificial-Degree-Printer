"""Evaluation module for comparing agent performance against baseline.

Defines functions to evaluate Q-Learning agents in self-play and against a random baseline.
Outputs metrics as dictionaries suitable for CSV export.
"""
from typing import Callable as _Callable
from typing import Dict as _Dict
from typing import Any as _Any
from typing import Union as _Union
from typing import Tuple as _Tuple
from typing import List as _List
import random as _unused_random
import random
from typing import Tuple, Dict, Any, Union, Callable
import numpy as np
from typing import Callable, Dict, Any, Union, Tuple, List
from dataclasses import dataclass
from datetime import datetime
SEED_BASELINE: int = 42
EPOCHES_PER_EVALUATION: int = 100

@dataclass
class EvalResults:
    """Container for evaluation results.

    Attributes:
        method_name: The agent or baseline being evaluated.
        win_rate_selfplay: Win rate in self-play (%).
        win_rate_vsb: Win rate vs baseline (%).
        draw_rate_selfplay: Draw rate in self-play (%).
        draw_rate_vsb: Draw rate vs baseline (%).
    """
    method_name: str
    win_rate_selfplay: float
    win_rate_vsb: float
    draw_rate_selfplay: float
    draw_rate_vsb: float

@dataclass
class EvalResults:
    """Container for evaluation results.

    Attributes:
        method_name: The agent or baseline being evaluated.
        win_rate_selfplay: Win rate in self-play (%).
        win_rate_vsb: Win rate vs baseline (%).
        draw_rate_selfplay: Draw rate in self-play (%).
        draw_rate_vsb: Draw rate vs baseline (%).
    """
    method_name: str
    win_rate_selfplay: float
    win_rate_vsb: float
    draw_rate_selfplay: float
    draw_rate_vsb: float

def get_seed() -> int:
    """Returns the base seed for reproducibility."""
    return SEED_BASELINE

class EvaluationError(Exception):
    """Raised when evaluation metrics computation fails."""
    pass

@dataclass
class EvalResults:
    """Container for evaluation results.
    
    Attributes:
        method_name: The agent or baseline being evaluated.
        win_rate_selfplay: Win rate in self-play (%).
        win_rate_vsb: Win rate vs baseline (%).
        draw_rate_selfplay: Draw rate in self-play (%).
        draw_rate_vsb: Draw rate vs baseline (%).
    """
    method_name: str
    win_rate_selfplay: float
    win_rate_vsb: float
    draw_rate_selfplay: float
    draw_rate_vsb: float

def evaluate_agent(env: Callable[[Any, Any], Tuple[Union[int, bool], List[Tuple[Any, int, ...]], Dict[str, Any]]], agent: Union[Callable[[Dict[str, Any]], Dict[str, Any]], 'RandomBaseline'], n_episodes: int, seed: int=42) -> EvalResults:
    """Evaluate an agent's performance.

    Evaluates the agent in both self-play and against a random baseline.
    Computes win and draw rates for each scenario.

    Args:
        env: The Tic-Tac-Toe environment factory function.
        agent: The agent class or instance to evaluate. Must support get_action(state, random_seed).
        n_episodes: Number of episodes to simulate for each metric calculation.
        seed: Random seed for baseline generation and episode shuffling.

    Returns:
        EvalResults: A dataclass containing win/draw rates for self-play and vs-baseline scenarios.
    """
    from src.evaluation import get_seed, RandomBaseline
    rng = np.random.RandomState(seed)
    baseline: RandomBaseline = RandomBaseline(get_seed())
    stats_selfplay: List[Tuple[int, int]] = []
    for _ in range(n_episodes):
        state, _, history = env(get_seed())
        winner = evaluate_episode(agent, agent, baseline, state, n_episodes=1)
        if winner == 1:
            stats_selfplay.append((1, 0))
        elif winner == -1:
            stats_selfplay.append((-1, 0))
        else:
            stats_selfplay.append((0, 0))
    agent_wins_self = sum((x[0] == 1 for x in stats_selfplay))
    draw_count_self = sum((x[0] == 0 for x in stats_selfplay))
    total_selfplay = len(stats_selfplay)
    win_rate_selfplay: float = agent_wins_self / total_selfplay * 100.0 if total_selfplay > 0 else 0.0
    draw_rate_selfplay: float = draw_count_self / total_selfplay * 100.0 if total_selfplay > 0 else 0.0
    stats_vsb: List[Tuple[int, int]] = []
    for _ in range(n_episodes):
        state, _, history = env(get_seed())
        winner = evaluate_episode(agent, baseline, baseline, state, n_episodes=1)
        if winner == 1:
            stats_vsb.append((1, 0))
        elif winner == -1:
            stats_vsb.append((-1, 0))
        else:
            stats_vsb.append((0, 0))
    agent_wins_vsb = sum((x[0] == 1 for x in stats_vsb))
    draw_count_vsb = sum((x[0] == 0 for x in stats_vsb))
    total_vsb = len(stats_vsb)
    win_rate_vsb: float = agent_wins_vsb / total_vsb * 100.0 if total_vsb > 0 else 0.0
    draw_rate_vsb: float = draw_count_vsb / total_vsb * 100.0 if total_vsb > 0 else 0.0
    return EvalResults(method_name='Q-Learning Agent', win_rate_selfplay=win_rate_selfplay, win_rate_vsb=win_rate_vsb, draw_rate_selfplay=draw_rate_selfplay, draw_rate_vsb=draw_rate_vsb)

def evaluate_episode(agent1: Callable[[Dict[str, Any]], Dict[str, Any]], agent2: Callable[[Dict[str, Any]], Dict[str, Any]], baseline: 'RandomBaseline', state: Dict[str, Any], n_episodes: int=1) -> Tuple[int, Union[bool, None]]:
    """Simulate a single episode between two agents (or agent vs baseline).

    Args:
        agent1: First player strategy.
        agent2: Second player strategy.
        baseline: Random opponent used in 'vs-baseline' mode.
        state: Initial board state.
        n_episodes: Number of steps to simulate (usually 1 for full game).

    Returns:
        Tuple[final_board_state, result] where result is the winner (1 or -1) or None if draw.
    """
    while True:
        action1 = agent1(state.get('board', [0] * 9))
        board = state.get('board', [[0] * 3 for _ in range(3)])
        r, c = action1[0]
        board[r][c] = 1
        state = {'board': board, 'done': False}
        if len(state['board']) > 9:
            break

class RandomBaseline:
    """Implementation of a uniform random opponent.

    Acts as the 'baseline' for comparison purposes.
    """

    def __init__(self, seed: int=42):
        """Initialize the baseline agent."""
        self.seed = seed

@dataclass
class EvalResults:
    """Container for evaluation results.

    Attributes:
        method_name: The agent or baseline being evaluated.
        win_rate_selfplay: Win rate in self-play (%).
        win_rate_vsb: Win rate vs baseline (%).
        draw_rate_selfplay: Draw rate in self-play (%).
        draw_rate_vsb: Draw rate vs baseline (%).
    """
    method_name: str
    win_rate_selfplay: float
    win_rate_vsb: float
    draw_rate_selfplay: float
    draw_rate_vsb: float

class RandomBaseline:
    """Implementation of a uniform random opponent.

    Acts as the 'baseline' for comparison purposes.
    """

    def __init__(self, seed: int=42):
        """Initialize the baseline agent."""
        self.seed = seed

    def get_action(self, state: Dict[str, Any]) -> Tuple[Any, int]:
        """Returns a random valid move.

        Args:
            state: Current board state.

        Returns:
            Tuple of (move_coordinates, action_value). Action value is arbitrary for this agent.
        """
        rng = np.random.RandomState(self.seed)
        valid_moves = []
        player_idx = state.get('player', 0)
        board = np.array(state.get('board', [[0] * 9] * 3))
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    valid_moves.append((r, c))
        if not valid_moves:
            return (None, 0)
        move = rng.choice(valid_moves)
        return (move, 0.0)
import random as _unused_random
from typing import List as _List

@dataclass
class EvalResults:
    """Container for evaluation results.

    Attributes:
        method_name: The agent or baseline being evaluated.
        win_rate_selfplay: Win rate in self-play (%).
        win_rate_vsb: Win rate vs baseline (%).
        draw_rate_selfplay: Draw rate in self-play (%).
        draw_rate_vsb: Draw rate vs baseline (%).
    """
    method_name: str
    win_rate_selfplay: float
    win_rate_vsb: float
    draw_rate_selfplay: float
    draw_rate_vsb: float

@dataclass
class RandomBaseline:
    """Implementation of a uniform random opponent.

    Acts as the 'baseline' for comparison purposes.
    """

    def __init__(self, seed: int=42):
        """Initialize the baseline agent."""
        self.seed = seed
