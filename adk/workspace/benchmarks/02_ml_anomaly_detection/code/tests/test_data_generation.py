import numpy as np
from data_generation import generate_physio_data

def test_generate_physio_data_signature_and_types():
    """Test that the function signature matches the specification and returns correct types."""
    # Use integer inputs to avoid floating point precision issues with int conversion
    result = generate_physio_data(2, 100, 0.1)
    assert isinstance(result, dict), 'Return type must be a dictionary.'
    assert 'data' in result, "Dictionary must contain 'data' key."
    assert 'labels' in result, "Dictionary must contain 'labels' key."
    assert isinstance(result['data'], np.ndarray), "'data' must be a numpy array."
    assert result['data'].dtype == np.float64, "'data' dtype must be float64."
    assert isinstance(result['labels'], np.ndarray), "'labels' must be a numpy array."
    assert result['labels'].dtype == np.int8, "'labels' dtype must be int8."
    expected_shape = (100, 2)
    assert result['data'].shape == expected_shape, f"'data' shape must be {expected_shape}, got {result['data'].shape}."
    assert result['labels'].shape == expected_shape, f"'labels' shape must be {expected_shape}, got {result['labels'].shape}."

def test_generate_physio_data_determinism():
    """Test that the function is deterministic by running it twice with the same inputs."""
    result1 = generate_physio_data(3, 50, 0.0)
    result2 = generate_physio_data(3, 50, 0.0)
    assert np.array_equal(result1['data'], result2['data']), 'Results must be identical for deterministic seeding.'
    assert np.array_equal(result1['labels'], result2['labels']), 'Labels must be identical for deterministic seeding.'

def test_generate_physio_data_anomaly_labels():
    """Test that labels correctly indicate anomalies based on injected impulses."""
    # Use inputs where anomaly_rate results in exactly n_anomalies equal to total_elements (rate=1.0)
    # Total elements = 5 * 4 = 20. rate=1.0 -> n_anomalies=20.
    result = generate_physio_data(4, 5, 1.0)
    
    # Verify all labels are 1
    assert np.all(result['labels'] == 1), 'All elements must be anomalies when rate=1.0.'
    
    # Verify data values are modified (base + noise + anomaly injection)
    # Since we don't know exact noise, we check that the data is not just zero
    assert not np.all(result['data'] == 0), 'Data should contain signal and anomalies.'

def test_generate_physio_data_anomaly_count():
    """Test that anomaly count matches calculated expected value based on rate."""
    result = generate_physio_data(3, 10, 0.5)
    total_elements = result['data'].shape[0] * result['data'].shape[1]
    expected_anomaly_count = int(total_elements * result.get('anomaly_rate', 0.5))
    actual_anomaly_count = np.sum(result['labels'])
    
    # Handle case where rate results in zero anomalies (rounding down)
    if expected_anomaly_count == 0:
        assert actual_anomaly_count == 0, 'Anomaly count must be 0 when rate*total < 1.'
    else:
        assert actual_anomaly_count == expected_anomaly_count, f'Anomaly count should be {expected_anomaly_count}, got {actual_anomaly_count}.'

def test_generate_physio_data_edge_cases():
    """Test edge cases defined in the specification."""
    # Test minimal inputs as per spec
    result_min = generate_physio_data(1, 1, 0.0)
    assert result_min['data'].shape == (1, 1), 'Shape must be (1, 1) for min inputs.'
    assert result_min['labels'].shape == (1, 1), f"Labels shape must be (1, 1). Got {result_min['labels'].shape}."
    
    # Test zero anomaly rate
    result_zero_rate = generate_physio_data(2, 50, 0.0)
    expected_anomaly_count = int(result_zero_rate['data'].shape[0] * result_zero_rate['data'].shape[1] * 0.0)
    actual_anomaly_count = np.sum(result_zero_rate['labels'])
    assert actual_anomaly_count == expected_anomaly_count, f'Anomaly count should be {expected_anomaly_count} for rate 0.'
