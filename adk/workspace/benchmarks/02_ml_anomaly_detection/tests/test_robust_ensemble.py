from src.data_types import SignalSample, DetectionResult
from src.methods.robust_ensemble import RobustEnsemble
import numpy as np

def test_fit_does_not_crash():
    """Test that fit runs without error on a small multi-channel sample set."""
    n_channels = 2
    detector = RobustEnsemble(ensemble_size=2, threshold=3.0)
    samples: list[SignalSample] = []
    for i in range(2):
        sample = SignalSample(
            timestamps=np.array([1.0, 2.0]),
            channels=np.ones((n_channels, 2)),
            labels=np.array([0, 0])
        )
        samples.append(sample)
    
    # Explicitly assign variables used in assertions to avoid undefined name errors
    n_tested = 0
    if detector is not None:
        try:
            detector.fit(samples)
            n_tested += 1
        except Exception as e:
            raise AssertionError(f"Fit raised exception: {e}")
    
    assert n_tested == 1, "Fit should complete successfully without raising exceptions."
