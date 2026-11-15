"""
Experiment runner for Tic-Tac-Toe Q-Learning vs Random Baseline.
Orchestrates training, evaluation, and result aggregation across runs.
"""
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import pandas as pd
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
MetricName = str
Value = float
Metrics = Dict[MetricName, Value]
ResultTuple = Tuple[float, float, int]
NUM_EPOCHES_PER_EVALUATION: int = 5
EPOCHES_PER_TRAINING: int = 100
RANDOM_SEED: int = 42
N_RUNS: int = 30
AGENT_WIN_RATE_THRESHOLD: float = 0.6
BASELINE_WIN_RATE_TARGET: float = 0.33

def get_state_string(state: Tuple[int, ...]) -> str:
    """Convert a tuple state into a canonical string key for Q-table lookup."""
    return f'{state[0]}:{state[1]}:{state[2]}:{state[3]}:{state[4]}:{state[5]}:{state[6]}:{state[7]}:{state[8]}'

@dataclass
class RunResult:
    """Container for a single run's metrics."""
    seed: int = 0
    agent_avg_win_rate: float = 0.0
    baseline_avg_win_rate: float = 0.0
    agent_convergence_episodes: int = 0
    episode_details: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class AggregateResult:
    """Container for aggregated results across all runs."""
    agent_mean_win_rate: float = 0.0
    agent_std_win_rate: float = 0.0
    baseline_mean_win_rate: float = 0.0
    baseline_std_win_rate: float = 0.0

@dataclass
class TrainingProgress:
    """Intermediate state during training evaluation."""
    episode: int
    win_rate: float
    loss: float

def run_experiment() -> None:
    """
    Execute the main experiment loop: train, evaluate against baseline, save results.
    Reads settings from src/config.Config and writes to results/*.csv.
    """
    import os
    from pathlib import Path
    from datetime import datetime
    from src.config import Config
    cfg = Config()
    random_seed: int = cfg.random_seed
    n_runs: int = cfg.n_runs
    agent_win_rate_threshold: float = cfg.agent_win_rate_threshold
    baseline_win_rate_target: float = cfg.baseline_win_rate_target
    epochs_per_evaluation: int = cfg.epochs_per_evaluation
    project_root = Path(__file__).parent.parent
    results_dir_path_var: Path = project_root / 'results'
    now_stamp_var: str = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_dir_path: Path = results_dir_path_var / now_stamp_var
    csv_path: Path = results_dir_path / 'experiment_results.csv'
    results_dir_path.mkdir(parents=True, exist_ok=True)
    print(f'Starting experiment. Results will be saved to {csv_path}')
    print(f'Config: N_RUNS={n_runs}, RANDOM_SEED={random_seed}, EPOCHES_PER_EVALUATION={epochs_per_evaluation}')
    pass
