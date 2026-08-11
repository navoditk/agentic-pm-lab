import pytest

from src.analytics.curves import interpolate_curve


def test_interpolates_midpoint_linearly():
    assert interpolate_curve([1, 3], [4, 6], [2]) == [5]


def test_preserves_observed_tenor_rate():
    assert interpolate_curve([1, 2, 5], [4, 4.5, 5], [2]) == [4.5]


def test_rejects_extrapolation():
    with pytest.raises(ValueError, match="outside"):
        interpolate_curve([1, 2], [4, 5], [3])
