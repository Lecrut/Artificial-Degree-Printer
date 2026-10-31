import csv
import heapq
import math
import random
from pathlib import Path
import config


def generate_obstacle_grid(size: int = config.GRID_SIZE, density: float = config.OBSTACLE_DENSITY, seed: int = 42) -> list[list[int]]:
    rng = random.Random(seed)
    grid = [[0 for _ in range(size)] for _ in range(size)]
    for r in range(size):
        for c in range(size):
            if (r, c) in ((0, 0), (size - 1, size - 1)):
                continue
            if rng.random() < density:
                grid[r][c] = 1
    # Guarantee a clear corridor along perimeter fallback if random seed blocks all paths
    for i in range(size):
        grid[0][i] = 0
        grid[i][size - 1] = 0
    return grid


def octile_heuristic(a: tuple[int, int], b: tuple[int, int]) -> float:
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    return (dx + dy) + (math.sqrt(2.0) - 2.0) * min(dx, dy)


def search_grid(
    grid: list[list[int]],
    start: tuple[int, int],
    goal: tuple[int, int],
    heuristic_weight: float = 0.0,
) -> tuple[float, int]:
    """Run Dijkstra (heuristic_weight=0.0) or Weighted Octile A* (heuristic_weight>0.0). Returns (cost, expanded_nodes)."""
    n = len(grid)
    pq: list[tuple[float, float, tuple[int, int]]] = [(0.0, 0.0, start)]
    g_score: dict[tuple[int, int], float] = {start: 0.0}
    closed: set[tuple[int, int]] = set()
    expanded = 0

    neighbors = [
        (-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
        (-1, -1, math.sqrt(2.0)), (-1, 1, math.sqrt(2.0)),
        (1, -1, math.sqrt(2.0)), (1, 1, math.sqrt(2.0)),
    ]

    while pq:
        _, g, current = heapq.heappop(pq)
        if current in closed:
            continue
        closed.add(current)
        expanded += 1

        if current == goal:
            return g, expanded

        cr, cc = current
        for dr, dc, step_cost in neighbors:
            nr, nc = cr + dr, cc + dc
            if 0 <= nr < n and 0 <= nc < n and grid[nr][nc] == 0:
                nxt = (nr, nc)
                if nxt in closed:
                    continue
                tentative_g = g + step_cost
                if tentative_g < g_score.get(nxt, float("inf")):
                    g_score[nxt] = tentative_g
                    h = octile_heuristic(nxt, goal) * heuristic_weight
                    heapq.heappush(pq, (tentative_g + h, tentative_g, nxt))

    return float("inf"), expanded


def train_and_evaluate(csv_out_path: str | Path | None = None, seed: int = 42) -> dict[str, float]:
    dijkstra_expanded_list: list[int] = []
    astar_expanded_list: list[int] = []
    optimality_ratios: list[float] = []
    successes = 0

    start = (0, 0)
    goal = (config.GRID_SIZE - 1, config.GRID_SIZE - 1)

    for trial in range(config.TRIALS):
        grid = generate_obstacle_grid(config.GRID_SIZE, config.OBSTACLE_DENSITY, seed=seed + trial)
        cost_d, exp_d = search_grid(grid, start, goal, heuristic_weight=0.0)
        cost_a, exp_a = search_grid(grid, start, goal, heuristic_weight=config.HEURISTIC_WEIGHT)

        if math.isfinite(cost_d) and math.isfinite(cost_a):
            successes += 1
            dijkstra_expanded_list.append(exp_d)
            astar_expanded_list.append(exp_a)
            optimality_ratios.append(cost_d / cost_a if cost_a > 0 else 1.0)

    avg_d = sum(dijkstra_expanded_list) / max(1, len(dijkstra_expanded_list))
    avg_a = sum(astar_expanded_list) / max(1, len(astar_expanded_list))
    avg_opt = sum(optimality_ratios) / max(1, len(optimality_ratios))
    speedup = avg_d / avg_a if avg_a > 0 else 1.0
    succ_rate = successes / float(config.TRIALS)

    baseline_row = {
        "method": "baseline",
        "trials": float(config.TRIALS),
        "avg_expanded_nodes": round(avg_d, 1),
        "path_optimality": 1.0,
        "speedup_factor": 1.0,
        "success_rate": round(succ_rate, 2),
    }
    proposed_row = {
        "method": "proposed",
        "trials": float(config.TRIALS),
        "avg_expanded_nodes": round(avg_a, 1),
        "path_optimality": round(avg_opt, 3),
        "speedup_factor": round(speedup, 2),
        "success_rate": round(succ_rate, 2),
    }

    if csv_out_path is not None:
        out_p = Path(csv_out_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with out_p.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["method", "trials", "avg_expanded_nodes", "path_optimality", "speedup_factor", "success_rate"],
            )
            writer.writeheader()
            writer.writerow(baseline_row)
            writer.writerow(proposed_row)

    return proposed_row
