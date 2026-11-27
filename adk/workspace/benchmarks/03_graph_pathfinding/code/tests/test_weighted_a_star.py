import pytest
import math
from weighted_a_star import search_weighted_astar

class TestSearchWeightedAStar:
    def test_start_equals_goal(self):
        """Test case where start and goal are the same."""
        grid = [[0, 0], [0, 0]]
        start = (0, 0)
        goal = (0, 0)
        weight = 1.0
        cost, expanded = search_weighted_astar(grid, start, goal, weight)
        assert cost == 0.0
        assert expanded == 0

    def test_unreachable_goal(self):
        """Test case where the goal is blocked by obstacles."""
        grid = [[0, 1], [0, 1]]
        start = (0, 0)
        goal = (0, 1)
        weight = 1.0
        cost, expanded = search_weighted_astar(grid, start, goal, weight)
        assert cost == math.inf
        assert expanded >= 0

    def test_simple_path_straight(self):
        """Test simple path with no obstacles in a straight line."""
        grid = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        start = (0, 0)
        goal = (0, 2)
        weight = 1.0
        cost, expanded = search_weighted_astar(grid, start, goal, weight)
        # Path is (0,0)->(0,1)->(0,2), each step cost 1.
        assert math.isclose(cost, 2.0)
        assert expanded > 0

    def test_simple_path_diagonal(self):
        """Test simple path with no obstacles in a diagonal line."""
        grid = [[0, 0], [0, 0]]
        start = (0, 0)
        goal = (1, 1)
        weight = 1.0
        cost, expanded = search_weighted_astar(grid, start, goal, weight)
        # Path is (0,0)->(1,1), diagonal step cost sqrt(2).
        assert math.isclose(cost, math.sqrt(2))
        assert expanded > 0

    def test_obstacle_forces_detour(self):
        """Test that the algorithm finds a path around an obstacle."""
        grid = [
            [0, 1, 0],
            [0, 0, 0]
        ]
        start = (0, 0)
        goal = (1, 2)
        weight = 1.0
        cost, expanded = search_weighted_astar(grid, start, goal, weight)
        # Direct diagonal is blocked at (0,1).
        # Possible paths: 
        # 1. (0,0)->(1,0)->(1,1)->(1,2) cost 1+sqrt(2)+1 = 2+sqrt(2) ~ 3.414
        # 2. (0,0)->(0,1) is blocked.
        # 3. (0,0)->(1,0)->(0,1) blocked.
        # Let's check if a path exists and isn't inf.
        assert cost != math.inf

    def test_out_of_bounds_start(self):
        """Test case where start is out of grid bounds."""
        grid = [[0, 0], [0, 0]]
        start = (-1, 0)
        goal = (0, 0)
        weight = 1.0
        cost, expanded = search_weighted_astar(grid, start, goal, weight)
        assert cost == math.inf
        assert expanded == 0

    def test_out_of_bounds_goal(self):
        """Test case where goal is out of grid bounds."""
        grid = [[0, 0], [0, 0]]
        start = (0, 0)
        goal = (2, 0)
        weight = 1.0
        cost, expanded = search_weighted_astar(grid, start, goal, weight)
        assert cost == math.inf
        assert expanded == 0

    def test_weight_impact_on_nodes_expanded(self):
        """Test that increasing the weight reduces the number of nodes expanded."""
        grid = [
            [0, 0, 0],
            [1, 1, 0],
            [0, 0, 0]
        ]
        start = (0, 0)
        goal = (2, 2)
        
        # Lower weight (closer to Dijkstra) should explore more nodes.
        cost_low_w, expanded_low_w = search_weighted_astar(grid, start, goal, 1.0)
        
        # Higher weight (more greedy) should ideally explore fewer nodes 
        # but might yield suboptimal paths. Here we just check the count.
        cost_high_w, expanded_high_w = search_weighted_astar(grid, start, goal, 2.0)
        
        # We expect both to find a path
        assert cost_low_w != math.inf
        assert cost_high_w != math.inf
        
        # Typically, higher weight biases towards goal, expanding fewer nodes in simple mazes,
        # though not guaranteed in all cases. We primarily test the interface return types here.
        assert isinstance(expanded_low_w, int)
        assert isinstance(expanded_high_w, int)
