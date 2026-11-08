import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
import config
import core

class TestConfigConstants:
    """Verify configuration constants match thesis requirements."""

    def test_n_samples_type_and_value(self):
        assert isinstance(config.N_SAMPLES, int), 'N_SAMPLES must be an integer'
        assert config.N_SAMPLES == 600, f'Expected N_SAMPLES=600, got {config.N_SAMPLES}'

    def test_anomaly_ratio_type_and_value(self):
        assert isinstance(config.ANOMALY_RATIO, float), 'ANOMALY_RATIO must be a float'
        assert config.ANOMALY_RATIO == 0.08, f'Expected ANOMALY_RATIO=0.08, got {config.ANOMALY_RATIO}'

    def test_z_threshold_type_and_value(self):
        assert isinstance(config.Z_THRESHOLD, float), 'Z_THRESHOLD must be a float'
        assert config.Z_THRESHOLD == 2.4, f'Expected Z_THRESHOLD=2.4, got {config.Z_THRESHOLD}'

    def test_ensemble_trees_type_and_value(self):
        assert isinstance(config.ENSEMBLE_TREES, int), 'ENSEMBLE_TREES must be an integer'
        assert config.ENSEMBLE_TREES == 25, f'Expected ENSEMBLE_TREES=25, got {config.ENSEMBLE_TREES}'

class TestDatasetGeneration:
    """Verify synthetic bio-signal stream generation."""

    def test_generate_biosignal_dataset_shape(self):
        n = 100
        ratio = 0.1
        features, labels = core.generate_biosignal_dataset(n, ratio, seed=42)
        assert len(features) == n, f'Expected {n} samples, got {len(features)}'
        assert len(labels) == n, f'Expected {n} labels, got {len(labels)}'

    def test_generate_biosignal_dataset_anomaly_count(self):
        n = 200
        ratio = 0.15
        features, labels = core.generate_biosignal_dataset(n, ratio, seed=42)
        expected_anomalies = int(n * ratio)
        actual_anomalies = np.sum(labels == 1)
        assert actual_anomalies == expected_anomalies, f'Expected {expected_anomalies} anomalies, got {actual_anomalies}'

    def test_generate_biosignal_dataset_determinism(self):
        features1, labels1 = core.generate_biosignal_dataset(100, 0.1, seed=42)
        features2, labels2 = core.generate_biosignal_dataset(100, 0.1, seed=42)
        np.testing.assert_array_equal(features1, features2)
        np.testing.assert_array_equal(labels1, labels2)

class TestEvaluationPipeline:
    """Verify comparative evaluation and CSV output."""

    def test_train_and_evaluate_creates_csv(self, tmp_path):
        out_path = str(tmp_path / 'test_results.csv')
        core.train_and_evaluate(out_path, seed=42)
        assert Path(out_path).exists(), f'CSV file {out_path} was not created'

    def test_train_and_evaluate_csv_columns(self, tmp_path):
        out_path = str(tmp_path / 'test_results.csv')
        core.train_and_evaluate(out_path, seed=42)
        df = pd.read_csv(out_path)
        required_cols = ['method', 'precision', 'recall', 'f1_score', 'false_alarm_rate']
        for col in required_cols:
            assert col in df.columns, f'Missing column: {col}'

    def test_train_and_evaluate_method_rows(self, tmp_path):
        out_path = str(tmp_path / 'test_results.csv')
        core.train_and_evaluate(out_path, seed=42)
        df = pd.read_csv(out_path)
        methods = set(df['method'])
        assert 'baseline' in methods, "Missing 'baseline' method row"
        assert 'proposed' in methods, "Missing 'proposed' method row"

    def test_train_and_evaluate_proposed_f1_better_than_baseline(self, tmp_path):
        out_path = str(tmp_path / 'test_results.csv')
        core.train_and_evaluate(out_path, seed=42)
        df = pd.read_csv(out_path)
        baseline_f1 = df[df['method'] == 'baseline']['f1_score'].values[0]
        proposed_f1 = df[df['method'] == 'proposed']['f1_score'].values[0]
        assert proposed_f1 >= baseline_f1, f'Proposed F1 ({proposed_f1}) should be >= Baseline F1 ({baseline_f1})'

def generate_comparison_plot(csv_path: str='results.csv', out_path: str='figures/comparison_chart.png') -> None:
    """Generate comparison chart from evaluation results.

    Reads the output CSV and plots precision/recall/F1 for baseline vs proposed methods.
    Saves the figure to the specified output path.

    Args:
        csv_path: Path to the results CSV file.
        out_path: Destination path for the generated plot.
    """
    import matplotlib.pyplot as plt
    import pandas as pd
    df = pd.read_csv(csv_path)
    methods = df['method'].unique()
    metrics = ['precision', 'recall', 'f1_score']
    x = np.arange(len(methods))
    width = 0.25
    fig, ax = plt.subplots(figsize=(8, 6))
    for i, metric in enumerate(metrics):
        values = df.set_index('method').loc[methods, metric].values
        _bars = ax.bar(x + i * width, values, width, label=metric)
    ax.set_ylabel('Score')
    ax.set_title('Bio-Signal Anomaly Detection: Baseline vs Proposed')
    ax.set_xticks(x + width)
    ax.set_xticklabels(methods)
    ax.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()

def generate_comparison_plot(csv_path: str='results.csv', out_path: str='figures/comparison_chart.png') -> None:
    """Generate comparison chart from evaluation results.

    Reads the output CSV and plots precision/recall/F1 for baseline vs proposed methods.
    Saves the figure to the specified output path.

    Args:
        csv_path: Path to the results CSV file.
        out_path: Destination path for the generated plot.
    """
    import matplotlib.pyplot as plt
    import pandas as pd
    df = pd.read_csv(csv_path)
    methods = df['method'].unique()
    metrics = ['precision', 'recall', 'f1_score']
    x = np.arange(len(methods))
    width = 0.25
    fig, ax = plt.subplots(figsize=(8, 6))
    for i, metric in enumerate(metrics):
        values = df.set_index('method').loc[methods, metric].values
        _bars = ax.bar(x + i * width, values, width, label=metric)
    ax.set_ylabel('Score')
    ax.set_title('Bio-Signal Anomaly Detection: Baseline vs Proposed')
    ax.set_xticks(x + width)
    ax.set_xticklabels(methods)
    ax.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
