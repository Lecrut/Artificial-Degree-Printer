"""Heuristic functions for spatial grids."""

def octile_distance(start: tuple[int, int], goal: tuple[int, int]) -> float:
    """Calculate the octile distance between two points.

    Octile distance d(a,b) = max(dx, dy) + (sqrt(2) - 1) * min(dx, dy).

    >>> round(octile_distance((0, 0), (3, 4)), 4)
    5.2426
    >>> round(octile_distance((0, 0), (0, 0)), 4)
    0.0
    """
    x1, y1 = start
    x2, y2 = goal
    dx: float = abs(x1 - x2)
    dy: float = abs(y1 - y2)
    return max(dx, dy) + (2 ** 0.5 - 1) * min(dx, dy)
