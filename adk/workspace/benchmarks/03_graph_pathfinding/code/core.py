import csv
import heapq
import math
import random
from pathlib import Path
import config


def generate_obstacle_grid(size: int = getattr(config, "GRID_SIZE", 32), density: float = getattr(config, "OBSTACLE_DENSITY", 0.22), seed: int = 42) -> list[list[int]]:
    rng = random.Random(seed)
    grid = [[0 for _ in range(size)] for _ in range(size)]
    for r in range(size):
        for c in range(size):
            if (r, c) in ((0, 0), (size - 1, size - 1)):
                continue
            if rng.random() < density:
                grid[r][c] = 1
    for i in range(size):
        grid[0][i] = 0
        grid[i][size - 1] = 0
    return grid


def search_grid(
    grid: list[list[int]],
    start: tuple[int, int],
    goal: tuple[int, int],
    heuristic_weight: float = 0.0,
) -> tuple[float, int]:
    """Baseline uninformed Dijkstra search (high node expansion, no A* heuristic)."""
    n = len(grid)
    pq: list[tuple[float, tuple[int, int]]] = [(0.0, start)]
    dist: dict[tuple[int, int], float] = {start: 0.0}
    visited: set[tuple[int, int]] = set()
    expanded = 0

    neighbors = [
        (-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
        (-1, -1, math.sqrt(2.0)), (-1, 1, math.sqrt(2.0)),
        (1, -1, math.sqrt(2.0)), (1, 1, math.sqrt(2.0)),
    ]

    while pq:
        d, curr = heapq.heappop(pq)
        if curr in visited:
            continue
        visited.add(curr)
        expanded += 1
        if curr == goal:
            return d, expanded

        cr, cc = curr
        for dr, dc, cost in neighbors:
            nr, nc = cr + dr, cc + dc
            if 0 <= nr < n and 0 <= nc < n and grid[nr][nc] == 0:
                nxt = (nr, nc)
                nxt_d = d + cost
                if nxt not in dist or nxt_d < dist[nxt]:
                    dist[nxt] = nxt_d
                    heapq.heappush(pq, (nxt_d, nxt))
    return float("inf"), expanded


def train_and_evaluate(csv_out_path: str | Path | None = config.RESULTS_PATH, seed: int = config.SEED) -> dict[str, float]:
    grid = generate_obstacle_grid(seed=seed)
    n = len(grid)
    cost, exp = search_grid(grid, (0, 0), (n - 1, n - 1), 0.0)
    return {"baseline_expanded": float(exp), "path_cost": cost}
