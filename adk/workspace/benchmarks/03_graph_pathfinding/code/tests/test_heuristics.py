from heuristics import octile_distance

def test_octile_distance_non_zero():
    """Test: Calculate standard octile distance."""
    result = octile_distance((0, 0), (3, 4))
    assert round(result, 4) == 5.2426

def test_octile_distance_zero():
    """Test: Distance is zero when start and goal are the same."""
    result = octile_distance((0, 0), (0, 0))
    assert round(result, 4) == 0.0