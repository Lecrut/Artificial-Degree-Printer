"""Configuration module for Distributed Federated Machine Learning & Proximal Optimization system."""

from typing import Final

# Cluster Hyperparameters
NUM_CLIENTS: Final[int] = 10
DIRICHLET_ALPHA: Final[float] = 0.5
LOCAL_EPOCHS: Final[int] = 3
LEARNING_RATE: Final[float] = 0.05
MU_PROXIMAL: Final[float] = 0.01
ROUNDS: Final[int] = 25

# System Defaults
SEED: Final[int] = 42
STRAGGLER_DROPOUT_RATE: Final[float] = 0.25
CSV_OUTPUT_PATH: Final[str] = "results.csv"
FIGURE_OUTPUT_PATH: Final[str] = "figures/comparison_chart.pdf"
