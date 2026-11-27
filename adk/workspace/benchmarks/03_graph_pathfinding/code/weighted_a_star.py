"""Implements the proposed Weighted A* algorithm using the octile heuristic for pathfinding on 8-connected spatial grids."""
from heuristics import octile_distance
import heapq
import math

def search_weighted_astar(grid: list[list[int]], start: tuple[int, int], goal: tuple[int, int], weight: float) -> tuple[float, int]:
    """Executes the Weighted A* algorithm to find a path from start to goal on the provided grid. The grid is a 2D list of integers where 0 represents an empty cell and 1 represents an obstacle. Returns a tuple containing: 1) The total cost of the found path as a float, or infinity (math.inf) if no path exists; 2) The number of nodes expanded during the search as an integer. If start or goal are out of grid bounds, returns (inf, 0). If start equals goal, returns (0.0, 0). The algorithm uses a priority queue where the node value is g + weight * h, with g being the path cost from start and h being the octile distance heuristic to goal."""
    rows = len(grid)
    if rows == 0:
        return (math.inf, 0)
    cols = len(grid[0])

    if not (0 <= start[0] < rows and 0 <= start[1] < cols):
        return (math.inf, 0)
    if not (0 <= goal[0] < rows and 0 <= goal[1] < cols):
        return (math.inf, 0)

    if start == goal:
        return (0.0, 0)

    # Priority queue: (f_score, counter, position)
    # f_score = g + weight * h
    open_set: list[tuple[float, int, tuple[int, int]]] = []
    
    h_start = octile_distance(start, goal)
    g_start = 0.0
    f_start = g_start + weight * h_start
    heapq.heappush(open_set, (f_start, 0, start))
    
    counter = 1 # Tie-breaking counter
    
    came_from: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    g_score: dict[tuple[int, int], float] = {start: 0.0}
    closed_set: set[tuple[int, int]] = set()
    
    expanded_nodes = 0
    
    # Directions for 8-connected grid: (dx, dy)
    directions = [
        (1, 0), (-1, 0), (0, 1), (0, -1),  # Orthogonal
        (1, 1), (1, -1), (-1, 1), (-1, -1) # Diagonal
    ]
    
    while open_set:
        current_f, _, current_pos = heapq.heappop(open_set)
        
        if current_pos in closed_set:
            continue
            
        closed_set.add(current_pos)
        expanded_nodes += 1
        
        if current_pos == goal:
            # Reconstruct path to calculate exact cost (though g_score should be accurate)
            # We just return the g_score of the goal
            return (g_score[goal], expanded_nodes)
        
        for dx, dy in directions:
            neighbor_row = current_pos[0] + dx
            neighbor_col = current_pos[1] + dy
            
            # Check bounds
            if not (0 <= neighbor_row < rows and 0 <= neighbor_col < cols):
                continue
                
            # Check obstacles
            if grid[neighbor_row][neighbor_col] != 0:
                continue
                
            neighbor_pos = (neighbor_row, neighbor_col)
            
            if neighbor_pos in closed_set:
                continue
            
            # Cost of moving from current to neighbor
            if dx != 0 and dy != 0:
                step_cost = math.sqrt(2)
            else:
                step_cost = 1.0
            
            tentative_g = g_score[current_pos] + step_cost
            
            # If this path to neighbor is better than any previous one
            if neighbor_pos not in g_score or tentative_g < g_score[neighbor_pos]:
                came_from[neighbor_pos] = current_pos
                g_score[neighbor_pos] = tentative_g
                h_neighbor = octile_distance(neighbor_pos, goal)
                f_neighbor = tentative_g + weight * h_neighbor
                heapq.heappush(open_set, (f_neighbor, counter, neighbor_pos))
                counter += 1
    
    # No path found
    return (math.inf, expanded_nodes)
