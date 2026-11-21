"""Entrypoint for the pathfinding experiment."""
import csv
from config import SEED, GRID_SIZE, OBSTACLE_DENSITY, REPETITIONS, WEIGHT_A_STAR
from core import generate_obstacle_grid, search_grid
from weighted_a_star import WeightedAStar
from plots import plot_results

def run_experiment() -> None:
    """Runs Dijkstra and Weighted A* comparisons and saves to results.csv."""
    n_runs: int = REPETITIONS
    weight: float = WEIGHT_A_STAR
    size: int = GRID_SIZE
    density: float = OBSTACLE_DENSITY
    seed_base: int = SEED
    
    dijkstra_costs: list[float] = []
    dijkstra_expanded: list[int] = []
    wa_costs: list[float] = []
    wa_expanded: list[int] = []
    
    import random
    for r in range(n_runs):
        current_seed: int = seed_base + r
        grid = generate_obstacle_grid(size, density, current_seed)
        start = (0, 0)
        goal = (size - 1, size - 1)
        
        # Dijkstra
        path_dijk, cost_dijk, expanded_dijk = search_grid(grid, start, goal)
        dijkstra_costs.append(cost_dijk)
        dijkstra_expanded.append(expanded_dijk)
        
        # Weighted A*
        algo_wa = WeightedAStar(start, goal, weight)
        cost_wa, expanded_wa = algo_wa.solve(grid)
        wa_costs.append(cost_wa)
        wa_expanded.append(expanded_wa)

    def calc_mean(vals: list[float]) -> float:
        return sum(vals) / len(vals)

    def calc_std(vals: list[float]) -> float:
        mean_val = calc_mean(vals)
        variance = sum(((x - mean_val) ** 2 for x in vals)) / len(vals)
        return variance ** 0.5
    
    rows: list[tuple[str, str, float]] = []
    
    # Dijkstra Results
    mean_d_cost = calc_mean(dijkstra_costs)
    std_d_cost = calc_std(dijkstra_costs)
    rows.append(('Dijkstra', 'path_cost', mean_d_cost))
    rows.append(('Dijkstra', 'expanded_nodes', float(calc_mean(dijkstra_expanded))))
    
    # Weighted A* Results
    mean_wa_cost = calc_mean(wa_costs)
    std_wa_cost = calc_std(wa_costs)
    rows.append(('WeightedA*', 'path_cost', mean_wa_cost))
    rows.append(('WeightedA*', 'expanded_nodes', float(calc_mean(wa_expanded))))
    
    with open('results.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['method', 'metric', 'value'])
        for row in rows:
            writer.writerow(row)
    
    plot_results()
