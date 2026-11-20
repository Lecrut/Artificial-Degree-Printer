from src.synthetic_data import SyntheticDataset
import numpy as np

def test_init_shape_and_attributes():
    """Test constructor parameters and generated shape."""
    dataset = SyntheticDataset(n_samples=100, n_channels=4, noise_std=0.1, anomaly_rate=0.05)
    assert hasattr(dataset, 'n_samples')
    assert hasattr(dataset, 'n_channels')
    assert hasattr(dataset, 'noise_std')
    assert hasattr(dataset, 'anomaly_rate')
    assert dataset.n_samples == 100
    assert dataset.n_channels == 4
    assert dataset.noise_std == 0.1
    assert dataset.anomaly_rate == 0.05

def test_generate_signature():
    """Test that generate method exists and has correct signature."""
    dataset = SyntheticDataset(n_samples=100, n_channels=4, noise_std=0.1, anomaly_rate=0.05)
    assert hasattr(dataset, 'generate')
    assert callable(dataset.generate)

def test_generate_output_shape():
    """Test that generate returns data with expected shape based on n_samples and n_channels."""
    dataset = SyntheticDataset(n_samples=100, n_channels=4, noise_std=0.1, anomaly_rate=0.05)
    result = dataset.generate(seed=42)
    assert isinstance(result, tuple), f'Expected tuple, got {type(result)}'
    assert len(result) == 2
    X, y = result
    assert isinstance(X, np.ndarray)
    assert X.shape == (100, 4)
    assert isinstance(y, np.ndarray)
    assert y.shape == (100,)
