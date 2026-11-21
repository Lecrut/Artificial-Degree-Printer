import heapq
import math
import random

import config


def generate_obstacle_grid(
    size: int = config.GRID_SIZE, density: float = config.OBSTACLE_DENSITY, seed: int = config.SEED
) -> list[list[int]]:
    """A seeded size x size grid: 1 is an obstacle, 0 a free cell; the top row and the right column stay free."""
    rng = random.Random(seed)
    grid = [[1 if rng.random() < density else 0 for _ in range(size)] for _ in range(size)]
    for i in range(size):
        grid[0][i] = 0
        grid[i][size - 1] = 0
    return grid


def search_grid(grid: list[list[int]], start: tuple[int, int], goal: tuple[int, int]) -> tuple[float, int]:
    """Dijkstra search on the 8-connected grid (straight step 1, diagonal sqrt(2)): (path cost, expanded nodes),
    or (inf, expanded nodes) when the goal is unreachable."""
    n = len(grid)
    pq: list[tuple[float, tuple[int, int]]] = [(0.0, start)]
    dist: dict[tuple[int, int], float] = {start: 0.0}
    visited: set[tuple[int, int]] = set()
    expanded = 0
    neighbors = [
        (-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
        (-1, -1, math.sqrt(2.0)), (-1, 1, math.sqrt(2.0)), (1, -1, math.sqrt(2.0)), (1, 1, math.sqrt(2.0)),
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
                nxt, nxt_d = (nr, nc), d + cost
                if nxt not in dist or nxt_d < dist[nxt]:
                    dist[nxt] = nxt_d
                    heapq.heappush(pq, (nxt_d, nxt))
    return float("inf"), expanded
