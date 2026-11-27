"""Provides the octile distance heuristic function for 8-connected spatial grids."""

def octile_distance(pos1: tuple[int, int], pos2: tuple[int, int]) -> float:
    """Computes the octile distance between two grid positions.

    The result represents the minimum number of steps to move from pos1 to pos2 on an
    infinite unobstructed 8-connected grid (where diagonal moves cost sqrt(2) and orthogonal
    moves cost 1). Returns a non-negative float equal to max(dx, dy) + (sqrt(2) - 1) * min(dx, dy),
    where dx is the absolute difference in x-coordinates and dy is the absolute difference in y-coordinates.
    For pos1 == pos2, returns 0.0.
    """
    import math
    dx: int = abs(pos1[0] - pos2[0])
    dy: int = abs(pos1[1] - pos2[1])
    min_val: float = min(dx, dy)
    max_val: float = max(dx, dy)
    return max_val + (math.sqrt(2) - 1.0) * min_val
