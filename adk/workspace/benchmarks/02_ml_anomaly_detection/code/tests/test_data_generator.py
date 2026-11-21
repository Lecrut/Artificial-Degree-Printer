from src.data_generator import generate_signal, get_ground_truth_mask

def test_generate_signal_shape_and_values():
    """Verify signal shape and value range per specification example."""
    X, anom = generate_signal(2, 10, 1, seed=0)
    assert X.shape == (2, 10), f'Expected shape (2, 10), got {X.shape}'
    assert -1 <= X.min() and X.max() <= 1, 'Signal values should be within [-1, 1]'

def test_get_ground_truth_mask():
    """Verify anomaly mask structure overlaps correctly."""
    anomalies = [{'channel': 0, 'start': 2, 'end': 5}]
    signal_length = 10
    n_channels = 2
    mask = get_ground_truth_mask(anomalies, signal_length, n_channels)
    assert len(mask) == (signal_length * n_channels,), f'Expected length {signal_length * n_channels}, got {len(mask)}'
    expected_anomaly_idx = range(2, 5)
    for idx in expected_anomaly_idx:
        assert mask[idx] == True, f'Mask index {idx} should be True'
