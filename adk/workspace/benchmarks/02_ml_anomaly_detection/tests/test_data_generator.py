import numpy as np
from src.data_generator import generate_sample, generate_dataset
from src.config import get_channels, get_noise_levels, get_anomaly_rate, get_seeds, get_ensemble_size
from src.data_types import SignalSample

def test_generate_sample_shape():
    """Test that generate_sample returns the correct shape for timestamps and channels."""
    from src.data_generator import generate_sample
    from src.config import get_channels, get_noise_levels, get_anomaly_rate, get_seeds
    from src.data_types import SignalSample
    channel = get_channels()[0]
    noise_level = get_noise_levels()[0]
    anomaly_rate = get_anomaly_rate()
    seed = 42
    sample = generate_sample(channel, noise_level, anomaly_rate, seed)
    assert isinstance(sample, SignalSample)
    expected_ts_len = 100
    actual_ts_len = len(sample.timestamps)
    assert actual_ts_len == expected_ts_len, f'Expected {expected_ts_len} timestamps, got {actual_ts_len}'
    expected_ch_len = 1
    actual_ch_len = len(sample.channels)
    assert actual_ch_len == expected_ch_len, f'Expected {expected_ch_len} channel for single-sample gen, got {actual_ch_len}'

def test_generate_sample_labels():
    """Test that labels are generated with the specified anomaly rate."""
    from src.data_generator import generate_sample
    from src.config import get_channels, get_noise_levels, get_anomaly_rate
    import numpy as np
    channel = get_channels()[0]
    noise_level = get_noise_levels()[0]
    anomaly_rate = get_anomaly_rate()
    seed = 42
    sample = generate_sample(channel, noise_level, anomaly_rate, seed)
    expected_len = 100
    assert len(sample.labels) == expected_len
    n_true_positive = np.sum(sample.labels)
    expected_tp_count = int(expected_len * anomaly_rate)
    assert abs(n_true_positive - expected_tp_count) <= 1, f'Expected ~{expected_tp_count} anomalies, got {n_true_positive}'

def test_generate_sample_anomaly_indices():
    """Test that generate_sample returns anomaly indices if available."""
    from src.data_generator import generate_sample
    from src.config import get_channels, get_noise_levels, get_anomaly_rate
    channel = get_channels()[0]
    noise_level = get_noise_levels()[0]
    anomaly_rate = get_anomaly_rate()
    seed = 42
    sample = generate_sample(channel, noise_level, anomaly_rate, seed)
    if hasattr(sample, 'anomaly_indices'):
        assert sample.anomaly_indices is not None or isinstance(sample.anomaly_indices, list)
        if sample.anomaly_indices is not None:
            for idx in sample.anomaly_indices:
                assert idx < len(sample.labels), f'Index {idx} out of bounds'
                assert sample.labels[idx] == 1, f'Label at index {idx} should be 1 (anomaly) but was {sample.labels[idx]}'

def test_generate_dataset_structure():
    """Test that generate_dataset returns a list of samples with consistent structure."""
    from src.data_generator import generate_dataset
    from src.config import get_channels, get_noise_levels, get_seeds
    from src.data_types import SignalSample
    channels = get_channels()
    noise_levels = get_noise_levels()
    n_samples = 10
    seeds = get_seeds()
    dataset = generate_dataset(channels, noise_levels, n_samples, seeds)
    assert isinstance(dataset, list)
    assert len(dataset) == n_samples
    first_sample = dataset[0]
    expected_ts_len = len(first_sample.timestamps)
    for i, sample in enumerate(dataset):
        assert isinstance(sample, SignalSample)
        assert len(sample.timestamps) == expected_ts_len
        expected_n_channels = 1
        actual_ch_len = len(sample.channels)
        assert actual_ch_len == expected_n_channels, f'Sample {i}: Expected {expected_n_channels} channel per sample, got {actual_ch_len}'
