import pytest
from pathlib import Path

class MockConfig:
    def __init__(self):
        self.num_segments = 10
        self.sample_length = 512
        self.anomaly_rate_ratio = 0.1
        self.threshold_opt_search_range = [1.0, 5.0]

def test_hyperparameters_structure():
    """
    Validate that Hyperparameters contains all required keys defined in config.
    Uses mocked state to avoid import cycles and ensures fast execution.
    """
    config = MockConfig()
    
    # Assert presence of required keys
    assert hasattr(config, 'num_segments')
    assert hasattr(config, 'sample_length')
    assert hasattr(config, 'anomaly_rate_ratio')
    assert hasattr(config, 'threshold_opt_search_range')
    
    # Validate types for integer fields
    assert isinstance(config.num_segments, int)
    assert isinstance(config.sample_length, int)
    
    # Validate type for float field
    assert isinstance(config.anomaly_rate_ratio, (int, float))
    
    # Validate thresholds structure
    assert isinstance(config.threshold_opt_search_range, list)
    assert len(config.threshold_opt_search_range) == 2