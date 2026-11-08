"""
config.py
Hyperparameters for Distributed Federated Machine Learning & Proximal Optimization.
Reference: IEEE Conference Paper Thesis Implementation (Artykuł Naukowy).
"""

import sys
from pathlib import Path

# --- Cluster Configuration ---
NUM_CLIENTS: int = 10
"""Total number of clients in the federated cluster."""

LOCAL_EPOCHS: int = 3
"""Number of local SGD epochs per client per communication round."""

ROUNDS: int = 25
"""Total number of federated communication rounds."""

# --- Optimization Hyperparameters ---
LEARNING_RATE: float = 0.05
"""Base learning rate for local SGD optimization."""

MU_PROXIMAL: float = 0.01
r"""Proximal term coefficient (\mu) for FedProx regularization."""

# --- Data Partitioning ---
DIRICHLET_ALPHA: float = 0.5
"""Dirichlet distribution parameter for non-IID data partitioning."""

N_SAMPLES_PER_CLIENT: int = 100
"""Base number of samples per client for synthetic dataset generation."""

N_CLASSES: int = 4
"""Number of target classes for the synthetic classification task."""

N_FEATURES: int = 10
"""Dimensionality of feature vectors."""

# --- Simulation Parameters ---
STRAGGLER_RATE: float = 0.25
"""Probability of a client dropping out (straggler) in any given round."""

SEED: int = 42
"""Global random seed for reproducibility across all components."""

# --- File Paths ---
ROOT_DIR: Path = Path(__file__).resolve().parent
FIGURES_DIR: Path = ROOT_DIR / "figures"
RESULTS_PATH: Path = ROOT_DIR / "results.csv"

# Ensure directories exist
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
