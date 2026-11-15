"""Configuration constants for the Tic-Tac-Toe Q-Learning experiment."""
import os
from pathlib import Path
from typing import List
from enum import Enum

class GameAgentType(Enum):
    """Enum representing the type of the opponent agent."""
    RANDOM = 'random'
    QLEARNER = 'q_learner'

class ExperimentConfig:
    """Main configuration object containing all experiment parameters."""

    def __init__(self, seed: int=42, num_runs: int=10, episodes_per_train: int=10000, num_evaluation_episodes: int=50, max_turns: int=9, discount_factor: float=0.9, learning_rate: float=0.2, epsilon_start: float=0.1, epsilon_end: float=0.0, epsilon_decay: float=0.995, reward_win: float=1.0, reward_loss: float=-1.0, reward_draw: float=0.0, output_dir: Path=Path('results')) -> None:
        """Initialize the experiment configuration with all parameters.

        Returns:
            None
        """
        self.seed = seed
        self.num_runs = num_runs
        self.episodes_per_train = episodes_per_train
        self.num_evaluation_episodes = num_evaluation_episodes
        self.max_turns = max_turns
        self.discount_factor = discount_factor
        self.learning_rate = learning_rate
        self.epsilon_start = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.reward_win = reward_win
        self.reward_loss = reward_loss
        self.reward_draw = reward_draw
        self.output_dir = output_dir

def get_default_config() -> ExperimentConfig:
    """Returns a copy of the default experiment configuration."""
    return ExperimentConfig()
'Configuration constants for the Tic-Tac-Toe Q-Learning experiment.'
import os
from pathlib import Path
from typing import List

class GameAgentType(Enum):
    """Enum representing the type of the opponent agent."""
    RANDOM = 'random'
    QLEARNER = 'q_learner'

class ExperimentConfig:
    """Main configuration object containing all experiment parameters."""

    def __init__(self) -> None:
        self.output_dir: Path = Path('./results')
        self.results_csv_path: Path = self.output_dir / 'experiment_results.csv'
        self.figures_dir: Path = Path('./figures')
        self.chart_path: Path = self.figures_dir / 'comparison_chart.pdf'
        self.png_chart_path: Path = self.figures_dir / 'comparison_chart.png'
        self.arch_diagram_path: Path = self.figures_dir / 'architecture_diagram.fig'
        self.available_figures: List[str] = [str(self.chart_path), str(self.png_chart_path)]
        self.seed_base: int = 42
        self.num_runs: int = 10
        self.max_episodes_per_training: int = 1000
        self.budget_step: int = 1
        self.win_rate_threshold: float = 0.8
        self.draw_rate_threshold: float = 0.2
        self.loss_rate_threshold: float = 0.05
        self.convergence_epsilon: float = 0.01
        self.max_convergence_steps: int = self.max_episodes_per_training // 10
        self.metrics_to_report: List[str] = ['win_rate_vs_random', 'draw_rate_vs_random', 'loss_rate_vs_random', 'training_convergence_step']

def get_default_config() -> ExperimentConfig:
    """Returns a copy of the default experiment configuration."""
    return ExperimentConfig()
