"""
Configuration constants and deterministic grid generation for pathfinding benchmarks.
"""

from __future__ import annotations

import random
import math
from typing import List, Tuple

# --- Hyperparameters & Config ---

# Grid dimensions (referenced in thesis as \ref_ast{config.py:GRID_SIZE})
# Rationale: 32x32 provides sufficient pathfinding complexity (approx. 10^9 potential paths)
# while allowing for rapid execution of hundreds of trials necessary for statistical significance.
GRID_SIZE: int = 32

# Obstacle generation parameter (density)
# Rationale: 0.22 (22%) density strikes a balance between connectivity and complexity,
# preventing fully connected grids (too easy) or disconnected graphs (too many failures).
OBSTACLE_DENSITY: float = 0.22

# Heuristic weight for Weighted A*.
# Rationale: w=1.15 provides an optimistic overestimation to bias search toward the goal,
# typically reducing expanded nodes by 30-50% compared to standard A*, while maintaining
# a bounded suboptimality of at most 15% (theoretical bound). Referenced in thesis as \ref_ast{config.py:HEURISTIC_WEIGHT}.
HEURISTIC_WEIGHT: float = 1.15

# Number of independent trials for statistical significance.
# Rationale: >30 trials required to satisfy Central Limit Theorem assumptions for
# mean and variance calculations in the academic evaluation.
TRIALS: int = 40


def generate_grid(seed: int = 42) -> List[List[int]]:
    """
    Generate a deterministic grid map with obstacles.

    Args:
        seed: Random seed for reproducibility.

    Returns:
        A 2D list representing the grid where 0 is free space and 1 is an obstacle.
    """
    rng = random.Random(seed)
    grid: List[List[int]] = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
    
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if rng.random() < OBSTACLE_DENSITY:
                grid[r][c] = 1
                
    # Ensure start (0,0) and goal (GRID_SIZE-1, GRID_SIZE-1) are free
    grid[0][0] = 0
    grid[GRID_SIZE - 1][GRID_SIZE - 1] = 0
    
    return grid


def octile_heuristic(u: Tuple[int, int], v: Tuple[int, int]) -> float:
    """
    Compute the octile distance heuristic between two points.

    h(n) = D * (|dx| + |dy|) + (D2 - D * 2) * min(|dx|, |dy|)
    where D=1, D2=sqrt(2). Simplified: sqrt(2)*min(dx, dy) + abs(dx-dy).

    This heuristic is admissible for 8-way movement (diagonal allowed).

    Args:
        u: Start coordinates (row, col).
        v: Goal coordinates (row, col).

    Returns:
        The estimated distance to the goal.
    """
    dx: int = abs(u[0] - v[0])
    dy: int = abs(u[1] - v[1])
    return (math.sqrt(2) - 2.0) * min(dx, dy) + (dx + dy)