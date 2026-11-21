import pytest
from weighted_a_star import WeightedAStar
import numpy as np

def test_neighbors_basic():
    """Test that neighbors method returns expected adjacent cells for a given position."""
    algo = WeightedAStar((0, 0), (5, 5), 1.5)
    neighbors_3_3 = algo.neighbors(3, 3)
    assert len(neighbors_3_3) > 0
    neighbors_0_0 = algo.neighbors(0, 0)
    expected_corner_count = 3
    assert len(neighbors_0_0) == expected_corner_count
    neighbors_0_1 = algo.neighbors(0, 1)
    expected_edge_count = 5
    assert len(neighbors_0_1) == expected_edge_count

def test_solve_basic():
    """Test that solve returns a valid path on an obstacle-free grid."""
    grid = np.ones((6, 6)) * 0.0
    algo = WeightedAStar((0, 0), (5, 5), 1.5)
    path = algo.solve(grid)
    assert path is not None
    assert len(path) > 1
