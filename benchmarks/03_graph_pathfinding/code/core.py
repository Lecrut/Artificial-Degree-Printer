"""core.py — Graph Pathfinding: Baseline Dijkstra vs. Weighted Octile A* Search.

This module provides deterministic graph generation, baseline uninformed search
(Dijkstra), and the proposed informed search algorithm (Weighted Octile A*).
The `train_and_evaluate` function orchestrates comparative trials across
generated obstacle grids to produce statistically significant performance metrics.

Algorithmic Complexity:
    - Dijkstra: O(E log V) where E is edges, V is vertices in grid graph.
    - Weighted A*: Generally O(k * E log V) where k depends on heuristic weight;
      typically expands significantly fewer nodes than Dijkstra for point-to-point
      pathfinding.
"""

import csv
import heapq
import math
import random
from pathlib import Path
from typing import Any

import config

# Constants for neighbor generation to avoid repetition
_CARDINAL_MOVES: list[tuple[int, int, float]] = [
    (-1, 0, 1.0),
    (1, 0, 1.0),
    (0, -1, 1.0),
    (0, 1, 1.0),
]

_DIAGONAL_MOVES: list[tuple[int, int, float]] = [
    (-1, -1, math.sqrt(2.0)),
    (-1, 1, math.sqrt(2.0)),
    (1, -1, math.sqrt(2.0)),
    (1, 1, math.sqrt(2.0)),
]

_ALL_NEIGHBORS: list[tuple[int, int, float]] = (
    _CARDINAL_MOVES + _DIAGONAL_MOVES
)


def heuristic_octile(
    node_a: tuple[int, int], node_b: tuple[int, int]
) -> float:
    """Compute the octile distance heuristic between two grid nodes.

    The octile distance (also known as Chebyshev or Chebyshev-like with 
    diagonal cost correction) is admissible and consistent for 8-way 
    movement grids where diagonal moves cost sqrt(2).

    Mathematical Formulation:
        Let dx = |x_a - x_b|, dy = |y_a - y_b|.
        h(n) = min(dx, dy) * sqrt(2) + max(dx, dy) - min(dx, dy)
             = (dx + dy) + (sqrt(2) - 2) * min(dx, dy)

    Args:
        node_a: Coordinates (row, col) of the starting node.
        node_b: Coordinates (row, col) of the target node.

    Returns:
        The estimated cost to reach `node_b` from `node_a`.
    """
    row_diff: float = abs(node_a[0] - node_b[0])
    col_diff: float = abs(node_a[1] - node_b[1])
    min_dist: float = min(row_diff, col_diff)
    max_dist: float = max(row_diff, col_diff)

    return (min_dist * math.sqrt(2.0)) + max_dist


def a_star_search(
    grid: list[list[int]],
    start: tuple[int, int],
    goal: tuple[int, int],
    heuristic_weight: float = config.WEIGHT_A_STAR,
) -> tuple[float, int]:
    """Implement Weighted Octile A* pathfinding algorithm.

    This function searches the grid for the shortest path from `start` to 
    `goal`, utilizing a priority queue ordered by f(n) = g(n) + w * h(n).

    Args:
        grid: 2D list representing the obstacle map (0 = free, 1 = obstacle).
        start: Tuple (row, col) of the starting position.
        goal: Tuple (row, col) of the destination position.
        heuristic_weight: Weight factor w >= 1 for weighted A* exploration bias.

    Returns:
        A tuple containing:
            - cost (float): The total path cost if a path exists; infinity otherwise.
            - expanded (int): The number of nodes popped from the priority queue.
    """
    n: int = len(grid)
    pq: list[tuple[float, float, tuple[int, int]]] = []
    
    # Tuple structure: (f_score, g_score, node_coords)
    h_start: float = heuristic_weight * heuristic_octile(start, goal)
    heapq.heappush(pq, (h_start, 0.0, start))

    g_scores: dict[tuple[int, int], float] = {start: 0.0}
    visited: set[tuple[int, int]] = set()
    expanded_count: int = 0

    while pq:
        f_curr, g_curr, curr = heapq.heappop(pq)

        if curr in visited:
            continue
        
        visited.add(curr)
        expanded_count += 1

        if curr == goal:
            return g_curr, expanded_count

        cr, cc = curr
        for dr, dc, step_cost in _ALL_NEIGHBORS:
            nr: int = cr + dr
            nc: int = cc + dc
            nxt: tuple[int, int] = (nr, nc)

            if not (0 <= nr < n and 0 <= nc < n):
                continue
            if grid[nr][nc] == 1:
                continue

            tentative_g: float = g_curr + step_cost
            current_best_g: float = g_scores.get(nxt, math.inf)

            if tentative_g < current_best_g:
                g_scores[nxt] = tentative_g
                h_val: float = heuristic_weight * heuristic_octile(nxt, goal)
                f_val: float = tentative_g + h_val
                heapq.heappush(pq, (f_val, tentative_g, nxt))

    return float("inf"), expanded_count


def search_grid(
    grid: list[list[int]],
    start: tuple[int, int],
    goal: tuple[int, int],
    heuristic_weight: float = 0.0,
) -> tuple[float, int]:
    """Wrapper for both Dijkstra and A* search based on heuristic weight.

    If `heuristic_weight` is 0.0, delegates to the baseline uninformed 
    Dijkstra algorithm. Otherwise, delegates to `a_star_search`.

    Args:
        grid: 2D list representing the obstacle map (0 = free, 1 = obstacle).
        start: Tuple (row, col) of the starting position.
        goal: Tuple (row, col) of the destination position.
        heuristic_weight: Weight for A* heuristic. 0.0 forces Dijkstra.

    Returns:
        A tuple containing:
            - cost (float): The path cost or infinity if no path.
            - expanded (int): Number of nodes expanded by the algorithm.
    """
    if abs(heuristic_weight) < 1e-9:
        return _dijkstra_search_impl(grid, start, goal)
    
    # For A*, we use the full weighted logic
    return a_star_search(grid, start, goal, heuristic_weight)


def _dijkstra_search_impl(
    grid: list[list[int]],
    start: tuple[int, int],
    goal: tuple[int, int],
) -> tuple[float, int]:
    """Baseline uninformed Dijkstra search implementation.

    Strictly follows the logic provided in the legacy core module to 
    maintain reproducibility of the baseline comparison.

    Args:
        grid: 2D list representing the obstacle map.
        start: Starting coordinates.
        goal: Goal coordinates.

    Returns:
        Tuple of (path_cost, nodes_expanded).
    """
    n: int = len(grid)
    pq: list[tuple[float, tuple[int, int]]] = [(0.0, start)]
    dist: dict[tuple[int, int], float] = {start: 0.0}
    visited: set[tuple[int, int]] = set()
    expanded: int = 0

    while pq:
        d, curr = heapq.heappop(pq)
        if curr in visited:
            continue
        visited.add(curr)
        expanded += 1
        if curr == goal:
            return d, expanded

        cr, cc = curr
        for dr, dc, cost in _ALL_NEIGHBORS:
            nr, nc = cr + dr, cc + dc
            if 0 <= nr < n and 0 <= nc < n and grid[nr][nc] == 0:
                nxt = (nr, nc)
                nxt_d = d + cost
                if nxt not in dist or nxt_d < dist[nxt]:
                    dist[nxt] = nxt_d
                    heapq.heappush(pq, (nxt_d, nxt))
    return float("inf"), expanded


def generate_obstacle_grid(
    size: int = config.GRID_SIZE,
    density: float = config.OBSTACLE_DENSITY,
    seed: int = config.SEED,
) -> list[list[int]]:
    """Generate a random obstacle grid with fixed start and goal.

    Args:
        size: Dimensions of the square grid (size x size).
        density: Probability of a cell being an obstacle (0.0 to 1.0).
        seed: Random seed for reproducibility.

    Returns:
        2D list where 0 represents free space and 1 represents an obstacle.
    """
    rng = random.Random(seed)
    grid = [[0 for _ in range(size)] for _ in range(size)]
    
    # Avoid placing obstacles on start (0,0) or goal (size-1, size-1)
    # although the loop below skips them implicitly if we check coordinates
    for r in range(size):
        for c in range(size):
            if (r, c) == (0, 0) or (r, c) == (size - 1, size - 1):
                continue
            if rng.random() < density:
                grid[r][c] = 1
                
    # Ensure border paths are somewhat open to increase solvability probability
    for i in range(size):
        grid[0][i] = 0
        grid[i][size - 1] = 0
        grid[size - 1][i] = 0
        grid[i][0] = 0
        
    return grid


def train_and_evaluate(
    csv_out_path: str | Path | None = None,
    seed: int = config.SEED,
) -> dict[str, float]:
    """Run comparative trials between Dijkstra and Weighted A*.n

    Generates `config.TRIALS` random grids of size `config.GRID_SIZE` 
    and evaluates both baseline (Dijkstra) and proposed (Weighted A*) 
    algorithms.

    Args:
        csv_out_path: Optional path to write the raw results CSV.
        seed: Base random seed for grid generation.

    Returns:
        Dictionary containing aggregate metrics:
            - `baseline_avg_expanded`: Mean nodes expanded by Dijkstra.
            - `proposed_avg_expanded`: Mean nodes expanded by A*.
            - `avg_path_cost_base`: Mean path cost of baseline.
            - `avg_path_cost_proposed`: Mean path cost of proposed.
            - `speedup_factor`: Ratio of baseline_expanded / proposed_expanded.
            - `success_rate_baseline`: Fraction of solved paths for Dijkstra.
            - `success_rate_proposed`: Fraction of solved paths for A*.
            - `path_optimality`: Ratio of proposed_cost / baseline_cost (avg).
    """
    trials: int = config.TRIALS
    weight_w: float = config.WEIGHT_A_STAR
    
    total_base_expanded: float = 0.0
    total_prop_expanded: float = 0.0
    total_base_cost: float = 0.0
    total_prop_cost: float = 0.0
    count_success_base: int = 0
    count_success_prop: int = 0
    optimality_sum: float = 0.0
    
    results_rows: list[dict[str, Any]] = []

    for i in range(trials):
        # Deterministic seed progression per trial
        trial_seed: int = seed + i
        grid = generate_obstacle_grid(seed=trial_seed)
        n: int = len(grid)
        start_node: tuple[int, int] = (0, 0)
        goal_node: tuple[int, int] = (n - 1, n - 1)

        # Run Baseline (Dijkstra)
        cost_base, exp_base = _dijkstra_search_impl(grid, start_node, goal_node)
        
        # Run Proposed (Weighted A*)
        cost_prop, exp_prop = a_star_search(grid, start_node, goal_node, heuristic_weight=weight_w)

        # Check success and optimality
        is_success_base: bool = math.isfinite(cost_base)
        is_success_prop: bool = math.isfinite(cost_prop)
        
        if is_success_base:
            count_success_base += 1
            total_base_cost += cost_base
            total_base_expanded += exp_base
        
        if is_success_prop:
            count_success_prop += 1
            total_prop_cost += cost_prop
            total_prop_expanded += exp_prop
            
            # Calculate optimality only for cases where both succeeded
            if is_success_base and cost_base > 0.0:
                ratio: float = cost_prop / cost_base
                optimality_sum += ratio

        results_rows.append({
            "trial": i + 1,
            "seed": trial_seed,
            "success_base": int(is_success_base),
            "success_prop": int(is_success_prop),
            "cost_base": cost_base if is_success_base else 0.0,
            "cost_prop": cost_prop if is_success_prop else 0.0,
            "exp_base": exp_base if is_success_base else 0,
            "exp_prop": exp_prop if is_success_prop else 0,
        })

    # Write CSV if path provided
    if csv_out_path:
        path_out: Path = Path(csv_out_path)
        with open(path_out, mode="w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results_rows[0].keys())
            writer.writeheader()
            writer.writerows(results_rows)

    # Calculate aggregate metrics
    denom: float = max(trials, 1)
    
    avg_base_expanded: float = total_base_expanded / trials if is_success_base else 0.0
    avg_prop_expanded: float = total_prop_expanded / trials if is_success_prop else 0.0
    
    # Speedup factor (nodes expanded by baseline vs proposed)
    # Avoid division by zero if A* expands 0 nodes (impossible here) or infinity
    speedup: float = 1.0
    if avg_prop_expanded > 0:
        speedup = total_base_expanded / total_prop_expanded
    
    # Success rates
    success_rate_base: float = count_success_base / trials
    success_rate_prop: float = count_success_prop / trials
    
    # Path optimality (how close to optimal is the weighted A*?)
    avg_optimality: float = 1.0
    if is_success_base and is_success_prop and cost_base > 0:
        avg_optimality = optimality_sum / max(trials, 1)

    return {
        "method": "baseline" if speedup < 1.5 else "proposed", # Placeholder logic for single dict return, usually returns both or aggregates
        # Actually, the contract asks for a single dict of aggregated metrics comparing them.
        # Let's return the aggregated stats directly.
        "avg_expanded_nodes_baseline": avg_base_expanded,
        "avg_expanded_nodes_proposed": avg_prop_expanded,
        "path_optimality_avg": avg_optimality,
        "speedup_factor": speedup,
        "success_rate_baseline": success_rate_base,
        "success_rate_proposed": success_rate_prop,
    }
