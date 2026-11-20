from src.baselines import UnivariateZScoreBaseline
import numpy as np


def test_predict_known_outliers():
    """Test that the baseline correctly identifies known outliers.

    Args:
        X: Data to predict on of shape (n_samples, n_features).

    Returns:
        Boolean array indicating anomalies of shape (n_samples,).

    Examples:
    >>> det = UnivariateZScoreBaseline(threshold=1.0)
    >>> det.fit(np.array([[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]]))
    >>> # Mean is [2, 2], std is approx [0.816, 0.816]
    >>> result = det.predict(np.array([[10.0, 10.0], [1.0, 1.0]]))
    >>> print(result)
    [ True  True]
    >>> result.shape
    (2,)
    """