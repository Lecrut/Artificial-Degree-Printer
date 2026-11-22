import numpy as np
from baseline_zscore import ZScoreBaseline


def test_init_default_threshold():
    """Verify default threshold is accessible and correct via __init__ args."""
    model = ZScoreBaseline()
    assert hasattr(model, 'threshold'), "Attribute 'threshold' must be present on ZScoreBaseline per specification"
    assert model.threshold == 3.0


def test_init_custom_threshold():
    """Verify custom threshold is set correctly via __init__ args."""
    model = ZScoreBaseline(threshold=5.0)
    assert hasattr(model, 'threshold'), "Attribute 'threshold' must be present on ZScoreBaseline per specification"
    assert model.threshold == 5.0


def test_fit_sets_mean_std_normal():
    """Test fit sets mean_ and std_ on normal data with non-zero variance."""
    X = np.array([[1.0, 2.0], [3.0, 6.0]])
    expected_mean = np.array([2.0, 4.0])
    # Numpy ddof=1 (sample std) for [[1, 2], [3, 6]]:
    # col 0: mean=2, var_sample=(1+1)/1 = 2 -> std=sqrt(2)
    # col 1: mean=4, var_sample=(4+4)/1 = 8 -> std=sqrt(8)
    expected_std = np.sqrt(np.array([2.0, 8.0]))
    
    model = ZScoreBaseline()
    model.fit(X)
    assert hasattr(model, 'mean_'), "Attribute 'mean_' must be present after fit per specification"
    assert hasattr(model, 'std_'), "Attribute 'std_' must be present after fit per specification"
    assert np.allclose(model.mean_, expected_mean)
    assert np.allclose(model.std_, expected_std)


def test_fit_sets_mean_std_zero_variance():
    """Test fit sets std_ to 0 for constant channels."""
    X = np.array([[1.0, 5.0], [1.0, 5.0]])
    expected_mean = np.array([1.0, 5.0])
    # With ddof=1, variance is 0/1 = 0.
    expected_std = np.array([0.0, 0.0])
    
    model = ZScoreBaseline()
    model.fit(X)
    assert hasattr(model, 'mean_')
    assert hasattr(model, 'std_')
    assert np.allclose(model.mean_, expected_mean)
    assert np.allclose(model.std_, expected_std)


def test_fit_sets_mean_std_constant_all():
    """Test fit sets correct mean and zero std for constant data."""
    X = np.array([[5.0, 5.0], [5.0, 5.0]])
    model = ZScoreBaseline()
    model.fit(X)
    assert hasattr(model, 'mean_')
    assert hasattr(model, 'std_')
    # mean is exactly [5.0, 5.0]
    # std with ddof=1 for 2 identical points: sqrt(( (5-5)^2 + (5-5)^2 ) / (2-1)) = 0
    assert np.allclose(model.mean_, [5.0, 5.0])
    assert np.allclose(model.std_, [0.0, 0.0])


def test_predict_normal_data():
    """Test predict returns 0 for data within threshold distance from mean."""
    X_train = np.array([[1.0], [2.0], [3.0]])
    # mean=2, std=sqrt(((1-2)^2+(2-2)^2+(3-2)^2)/2) = sqrt(2/2) = 1.0
    model = ZScoreBaseline(threshold=1.0)
    model.fit(X_train)
    X_test = np.array([[2.0]])
    # z-score of 2.0 is 0. |0| < 1.0 -> normal
    predictions = model.predict(X_test)
    assert predictions[0] == 0


def test_predict_anomalous_data():
    """Test predict returns 1 for data far from mean."""
    X_train = np.array([[1.0], [2.0], [3.0]])
    model = ZScoreBaseline(threshold=1.0)
    model.fit(X_train)
    X_test = np.array([[10.0]])
    # z-score of 10.0 is (10-2)/1 = 8. |8| > 1.0 -> anomalous
    predictions = model.predict(X_test)
    assert predictions[0] == 1


def test_predict_zero_std_channel():
    """Test predict handles channels with zero variance without crashing."""
    X_train = np.array([[1.0, 5.0], [3.0, 5.0]])
    # col 0: mean=2, std=sqrt((1+1)/1)=sqrt(2)
    # col 1: mean=5, std=0
    model = ZScoreBaseline(threshold=3.0)
    model.fit(X_train)
    X_test = np.array([[2.0, 5.0]])
    # col 0: z=(2-2)/sqrt(2) = 0
    # col 1: std is 0, value is exactly mean (5.0), so distance is 0. Usually handled as normal.
    predictions = model.predict(X_test)
    assert predictions[0] == 0


def test_predict_mixed_variance():
    """Test predict with mixed variance channels."""
    X_train = np.array([[1.0, 10.0], [2.0, 10.0]])
    # col 0: mean=1.5, std=sqrt((0.25+0.25)/1)=sqrt(0.5)
    # col 1: mean=10, std=0
    model = ZScoreBaseline(threshold=3.0)
    model.fit(X_train)
    X_test = np.array([[10.0, 10.0]])
    # col 0: z=(10-1.5)/sqrt(0.5) = 8.5/sqrt(0.5) approx 12 > 3
    # col 1: std=0, value=10=mean -> 0
    predictions = model.predict(X_test)
    assert predictions[0] == 1
