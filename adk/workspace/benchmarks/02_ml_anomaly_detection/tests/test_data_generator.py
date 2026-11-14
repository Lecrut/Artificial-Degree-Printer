import pytest
from pathlib import Path
import numpy as np
from typing import Tuple, List
from dataclasses import dataclass

class SignalConfig:
    num_channels: int = 3
    sample_length: int = 100
    num_segments: int = 5

@dataclass
class AnomalyConfig:
    anomaly_rate_ratio: float = 0.1
    injected_anomaly_types: List[str] = None

    def __post_init__(self):
        if self.injected_anomaly_types is None:
            self.injected_anomaly_types = ['spike', 'flatline']
from src.data.synthetic_data_generator import BioSignalGenerator, SignalConfig as Config_cls

class MockGenerator(BioSignalGenerator):

    def __init__(self, config: SignalConfig, anomaly_config: AnomalyConfig, rng_seed: int=42):
        self.config = config
        self.anomaly_config = anomaly_config
        self.rng_seed = rng_seed
        self._normal_samples = []

    def generate_normal_sample(self, length: int) -> np.ndarray:
        return np.zeros(length)

    def generate_anomaly_sample(self, start_idx: int, length: int) -> Tuple[np.ndarray, str]:
        return (np.ones(length), 'anomaly')

    def generate_dataset(self, num_segments: int) -> Tuple[List[np.ndarray], List[str]]:
        datasets = []
        labels = []
        for i in range(num_segments):
            datasets.append(np.zeros(self.config.sample_length))
            labels.append(f'segment_{i}')
        return (datasets, labels)

@pytest.mark.parametrize('sample_length', [128, 512])
def test_signal_config_dimensions(sample_length: int) -> None:
    """
    Test that SignalConfig accepts valid sample lengths.

    Args:
        sample_length (int): The length to test.
    """
    from src.data.synthetic_data_generator import SignalConfig, AnomalyConfig
    config = SignalConfig(sample_length=sample_length)
    assert config.sample_length == sample_length

def test_anomaly_config_defaults() -> None:
    """Verify injected anomaly types are set by default."""
    config = AnomalyConfig()
    expected_types = ['spike', 'flatline']
    assert config.injected_anomaly_types == expected_types

def test_mock_generator_init(config: SignalConfig) -> None:
    """
    Verify MockGenerator.__init__ parameters and return attributes.

    Args:
        config (SignalConfig): Configuration for the generator.
    """
    anomaly_config = AnomalyConfig()
    gen = MockGenerator(config, anomaly_config)
    assert hasattr(gen, 'config')
    assert hasattr(gen, 'anomaly_config')
    assert hasattr(gen, '_normal_samples')

@pytest.mark.parametrize('length', [10])
def test_mock_generate_normal_sample(length: int) -> None:
    """Verify generate_normal_sample returns zero array of correct shape."""
    gen = MockGenerator(SignalConfig(), AnomalyConfig())
    sample = gen.generate_normal_sample(length)
    assert isinstance(sample, np.ndarray)
    assert len(sample) == length
    assert np.allclose(sample, 0.0)

@pytest.mark.parametrize('length', [5])
def test_mock_generate_anomaly_sample(length: int) -> None:
    """Verify generate_anomaly_sample returns one array and string label."""
    gen = MockGenerator(SignalConfig(), AnomalyConfig())
    sample, label = gen.generate_anomaly_sample(0, length)
    assert isinstance(sample, np.ndarray)
    assert len(sample) == length
    assert np.allclose(sample, 1.0)
    assert isinstance(label, str)
    assert label == 'anomaly'

@pytest.mark.parametrize('num_segments', [5])
def test_mock_generate_dataset_structure(num_segments: int) -> None:
    """Verify generate_dataset returns list of arrays and labels."""
    gen = MockGenerator(SignalConfig(), AnomalyConfig())
    datasets, labels = gen.generate_dataset(num_segments)
    assert isinstance(datasets, List)
    assert isinstance(labels, List)
    assert len(datasets) == num_segments
    assert len(labels) == num_segments
    for i, d in enumerate(datasets):
        assert isinstance(d, np.ndarray)
        assert d.shape[0] == SignalConfig().sample_length