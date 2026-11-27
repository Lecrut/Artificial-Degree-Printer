"""Runs the comparative experiment between Dijkstra and Weighted A* across multiple seeds, grid configurations, and weights, saving results to CSV."""
import config
import core
import weighted_a_star
WEIGHTS: list[float] = [0.5, 1.0, 1.5, 2.0]
N_RUNS: int = 50

def run_experiment() -> None:
    """Executes the comparative experiment. It iterates over each weight in WEIGHTS, generates a grid using config parameters via core.generate_obstacle_grid, and for N_RUNS repetitions, calls core.search_grid (Dijkstra) and weighted_a_star.search_weighted_astar. It computes average expanded nodes (avg_expanded_nodes), standard deviation of expanded nodes (std_expanded_nodes), path cost for Dijkstra (path_cost_dijkstra), path cost for A* (path_cost_astar), and the suboptimality gap defined as (cost_astar - cost_dijkstra) / cost_dijkstra when a valid path exists, or 0.0 otherwise. It writes results to results.csv with columns: method, metric, value, std_dev, n_runs. Specifically, it writes rows for method='weighted_astar' and metric='suboptimality_gap' containing the aggregated suboptimality gap data across runs."""
    import csv
    import math
    import numpy as np
    grid_size: int = config.GRID_SIZE
    obstacle_density: float = config.OBSTACLE_DENSITY
    seed_base: int = config.SEED
    weights_list: list[float] = WEIGHTS
    n_runs: int = N_RUNS
