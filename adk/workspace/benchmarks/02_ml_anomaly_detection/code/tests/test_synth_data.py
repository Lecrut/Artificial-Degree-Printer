import numpy as np
from synth_data import generate_dataset


def test_determinism_of_generate_dataset():
    """Test determinism of generate_dataset."""
    n_samples = 100
    n_channels = 3
    anomaly_fraction = 0.1
    base_seed = 42
    result1 = generate_dataset(n_samples, n_channels, anomaly_fraction, base_seed)

    def convert_to_serializable(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif hasattr(obj, 'tolist'):
            return obj.tolist()
        else:
            return str(obj)
    
    result1_str = [convert_to_serializable(x) for x in result1]
    result2 = generate_dataset(n_samples, n_channels, anomaly_fraction, base_seed)
    result2_str = [convert_to_serializable(x) for x in result2]
    assert result1_str == result2_str, "Results must be identical for the same seed to ensure determinism"
