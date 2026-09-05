"""Terrain-derived indicators."""

import numpy as np


def calculate_slope(elevation: np.ndarray, cell_size: float = 1.0) -> np.ndarray:
    """Calculate slope in degrees from an elevation grid."""
    elevation_array = np.asarray(elevation, dtype=float)
    if elevation_array.ndim != 2:
        raise ValueError("elevation must be a two-dimensional array")
    if cell_size <= 0:
        raise ValueError("cell_size must be positive")
    gradient_y, gradient_x = np.gradient(elevation_array, cell_size, cell_size)
    return np.degrees(np.arctan(np.hypot(gradient_x, gradient_y)))