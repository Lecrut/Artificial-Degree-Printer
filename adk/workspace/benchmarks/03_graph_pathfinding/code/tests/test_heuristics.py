import math
import pytest

from heuristics import octile_distance


def test_octile_distance_same_position_returns_zero():
    """For pos1 == pos2, returns 0.0."""
    assert octile_distance((0, 0), (0, 0)) == 0.0
    assert octile_distance((5, 5), (5, 5)) == pytest.approx(0.0)


def test_octile_distance_diagonal_moves():
    """Tests movement purely in diagonal direction."""
    expected_diag = math.sqrt(2)
    assert octile_distance((0, 0), (1, 1)) == pytest.approx(expected_diag)


def test_octile_distance_orthogonal_moves():
    """Tests movement purely in orthogonal direction."""
    assert octile_distance((0, 0), (2, 0)) == 2.0
    assert octile_distance((0, 0), (0, 3)) == 3.0


def test_octile_distance_mixed_moves():
    """Tests mixed orthogonal and diagonal movement."""
    expected = 1 + 2 * math.sqrt(2)
    assert octile_distance((0, 0), (3, 2)) == pytest.approx(expected)


def test_octile_distance_negative_coordinates():
    """Tests movement involving negative coordinates."""
    expected = 2 * math.sqrt(2)
    assert octile_distance((-1, -1), (1, 1)) == pytest.approx(expected)


def test_octile_distance_non_negative_result():
    """The result represents a distance, so it must be non-negative."""
    assert octile_distance((0, 0), (10, 10)) >= 0
    assert octile_distance((10, 10), (0, 0)) >= 0
    assert octile_distance((-5, -5), (5, 5)) >= 0
