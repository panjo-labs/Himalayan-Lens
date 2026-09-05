"""Small deterministic fixtures for development without network access."""

import numpy as np

from config.scoring import LANDCOVER_SCORES, WEIGHTS
from indicators.ndvi import calculate_ndvi
from indicators.terrain import calculate_slope


def build_demo_scene(region: str) -> dict[str, object]:
    """Build a compact synthetic scene with realistic indicator ranges."""
    seed = sum(ord(character) for character in region)
    rng = np.random.default_rng(seed)
    rows, columns = 14, 18
    latitudes, longitudes = np.meshgrid(
        np.linspace(29.5, 31.3, rows),
        np.linspace(78.0, 80.3, columns),
        indexing="ij",
    )
    elevation = 650 + np.linspace(0, 2200, rows)[:, None] + rng.normal(0, 80, (rows, columns))
    slope = calculate_slope(elevation, cell_size=0.01)
    red = rng.uniform(0.12, 0.32, (rows, columns))
    nir = red + rng.uniform(0.08, 0.42, (rows, columns))
    ndvi = calculate_ndvi(red, nir)
    historical_ndvi = np.clip(ndvi + rng.normal(0.025, 0.025, (rows, columns)), -1, 1)
    classes = np.array(["forest", "agriculture", "grass-shrub", "bare", "built-up"])
    landcover = rng.choice(classes, size=(rows, columns), p=[0.36, 0.22, 0.2, 0.14, 0.08])
    landcover_component = np.vectorize(LANDCOVER_SCORES.get)(landcover)
    landcover_code = np.vectorize({name: index for index, name in enumerate(classes, start=1)}.get)(landcover)
    suitability = (
        WEIGHTS["slope"] * np.clip(100 - slope * 2.2, 0, 100)
        + WEIGHTS["vegetation"] * np.clip(100 - ndvi * 55, 0, 100)
        + WEIGHTS["landcover"] * landcover_component
        + WEIGHTS["change"] * np.clip(100 - np.abs(ndvi - historical_ndvi) * 300, 0, 100)
    )
    return {
        "region": region,
        "latitudes": latitudes,
        "longitudes": longitudes,
        "elevation": elevation,
        "slope": slope,
        "red": red,
        "nir": nir,
        "ndvi": ndvi,
        "historical_ndvi": historical_ndvi,
        "landcover": landcover,
        "landcover_code": landcover_code,
        "suitability": suitability,
    }