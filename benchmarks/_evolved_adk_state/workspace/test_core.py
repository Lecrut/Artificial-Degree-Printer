from pathlib import Path
import core


def test_astar_vs_dijkstra_pathfinding():
    grid = core.generate_obstacle_grid(16, 0.2, seed=42)
    cost_d, exp_d = core.search_grid(grid, (0, 0), (15, 15), heuristic_weight=0.0)
    cost_a, exp_a = core.search_grid(grid, (0, 0), (15, 15), heuristic_weight=1.15)
    assert exp_a < exp_d
    assert cost_a <= cost_d * 1.05
    csv_path = Path(__file__).resolve().parent / "results.csv"
    metrics = core.train_and_evaluate(csv_path, seed=42)
    assert metrics["speedup_factor"] >= 2.0
    assert metrics["path_optimality"] >= 0.98
    assert csv_path.exists()
