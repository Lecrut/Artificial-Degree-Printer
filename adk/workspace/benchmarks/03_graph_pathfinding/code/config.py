from __future__ import annotations

# ==============================================================================
# Section 1: Grid Environment Configuration
# Defines the topological space for pathfinding experiments.
# Symbolic Reference: \ref_ast{config.py:GRID_SIZE}
# ==============================================================================
GRID_SIZE: int = 32
OBSTACLE_DENSITY: float = 0.22

# ==============================================================================
# Section 2: Algorithm Hyperparameters (A* Optimization)
# Enforces W3 -> W4 -> W1 -> W2 execution loop order.
# Symbolic Reference: \ref_ast{config.py:HEURISTIC_WEIGHT}
# ==============================================================================
HEURISTIC_TYPE: str = "octile"
WEIGHT_A_STAR: float = 1.5
BASELINE_HEURISTIC_WEIGHT: float = 1.0
HEURISTIC_WEIGHT: float = 1.2

# ==============================================================================
# Section 3: Simulation & Experiment Configuration
# Standardizes reproducibility across all trials.
# ==============================================================================
TRIALS: int = 40
SEED: int = 42
