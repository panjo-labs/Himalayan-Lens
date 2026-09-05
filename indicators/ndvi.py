"""Vegetation index calculations."""

import numpy as np


def calculate_ndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """Calculate NDVI and return NaN where the spectral denominator is zero."""
    red_array = np.asarray(red, dtype=float)
    nir_array = np.asarray(nir, dtype=float)
    if red_array.shape != nir_array.shape:
        raise ValueError("red and nir arrays must have the same shape")
    denominator = nir_array + red_array
    with np.errstate(divide="ignore", invalid="ignore"):
        ndvi = np.divide(nir_array - red_array, denominator)
    return np.where(denominator == 0, np.nan, ndvi)