"""Weighted A* algorithm for spatial grids."""
from typing import Tuple
import heapq
import math
from heuristics import octile_distance

class WeightedAStar:
    """Implements weighted A* search on an obstacle grid.

    >>> algo = WeightedAStar((0,0), (5,5), 1.5)
    >>> len(algo.neighbors(3, 3)) > 0
    True
    """

    def __init__(self, start: tuple[int, int], goal: tuple[int, int], weight: float) -> None:
        """Initialize the searcher."""
        self.start = start
        self.goal = goal
        self.weight = weight
        self._rows = 100
        self._cols = 100

    def solve(self, grid: list[list[int]]) -> tuple[float, int]:
        """Run search. Returns (path_cost, expanded_nodes)."""
        self._rows = len(grid)
        self._cols = len(grid[0]) if self._rows > 0 else 0
        start_r, start_c = self.start
        goal_r, goal_c = self.goal
        counter = 0
        open_set: list[tuple[float, int, tuple[int, int]]] = []
        heapq.heappush(open_set, (0.0, counter, start_r, start_c))
        g_score: dict[tuple[int, int], float] = {(start_r, start_c): 0.0}
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        expanded_count = 0
        while open_set:
            f_current, _, curr_r, curr_c = heapq.heappop(open_set)
            current = (curr_r, curr_c)
            if current == self.goal:
                return (g_score[current], expanded_count)
            expanded_count += 1
            for dr, dc in directions:
                nr, nc = (curr_r + dr, curr_c + dc)
                neighbor = (nr, nc)
                if not (0 <= nr < self._rows and 0 <= nc < self._cols):
                    continue
                if grid[nr][nc] != 0:
                    continue
                if dr != 0 and dc != 0:
                    move_cost = math.sqrt(2)
                else:
                    move_cost = 1.0
                tentative_g = g_score[current] + move_cost
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    g_score[neighbor] = tentative_g
                    h_estimate = self.weight * octile_distance(neighbor, self.goal)
                    f_score = tentative_g + h_estimate
                    counter += 1
                    heapq.heappush(open_set, (f_score, counter, nr, nc))
        return (float('inf'), expanded_count)

    def neighbors(self, r: int, c: int) -> list[tuple[int, int]]:
        """Return valid neighbor coordinates for (r, c) within the current grid bounds.

    The grid bounds are set by calling solve() first or initialized to a default large size.
    """
        res = []
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for dr, dc in directions:
            nr, nc = (r + dr, c + dc)
            if 0 <= nr < self._rows and 0 <= nc < self._cols:
                res.append((nr, nc))
        return res
