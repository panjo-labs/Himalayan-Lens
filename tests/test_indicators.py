import numpy as np
import pytest

from indicators.ndvi import calculate_ndvi
from indicators.terrain import calculate_slope


def test_calculate_ndvi_matches_formula():
    assert np.allclose(calculate_ndvi(np.array([1.0]), np.array([3.0])), [0.5])


def test_calculate_ndvi_rejects_mismatched_shapes():
    with pytest.raises(ValueError):
        calculate_ndvi(np.ones((2, 2)), np.ones((2, 1)))


def test_flat_elevation_has_zero_slope():
    assert np.allclose(calculate_slope(np.ones((3, 3))), 0)


def test_slope_increases_on_steeper_surface():
    gentle = calculate_slope(np.arange(9, dtype=float).reshape(3, 3), cell_size=1)
    steep = calculate_slope(np.arange(9, dtype=float).reshape(3, 3) * 10, cell_size=1)
    assert steep.mean() > gentle.mean()