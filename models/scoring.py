"""Explainable suitability scoring independent of Streamlit."""

from dataclasses import dataclass

import numpy as np

from config.scoring import LANDCOVER_SCORES, THRESHOLDS, WEIGHTS


@dataclass(frozen=True)
class Assessment:
    score: float
    label: str
    reasons: tuple[str, ...]
    components: dict[str, float]

    def map_key(self, layer: str) -> str:
        return {"Suitability": "suitability", "NDVI": "ndvi", "Slope": "slope", "Elevation": "elevation", "Land cover": "landcover_code"}.get(layer, "suitability")


def _slope_score(slope: np.ndarray) -> float:
    return float(np.clip(100 - np.nanmean(slope) * 2.2, 0, 100))


def _vegetation_score(ndvi: np.ndarray) -> float:
    return float(np.clip(100 - np.nanmean(ndvi) * 55, 0, 100))


def _landcover_score(landcover: np.ndarray) -> float:
    scores = [LANDCOVER_SCORES.get(str(value), 0) for value in np.asarray(landcover).ravel()]
    return float(np.mean(scores))


def assess_scene(scene: dict[str, object]) -> Assessment:
    """Score a scene using provisional weights and transparent components."""
    required = {"slope", "ndvi", "landcover", "historical_ndvi"}
    missing = required.difference(scene)
    if missing:
        raise ValueError(f"scene is missing required indicators: {sorted(missing)}")
    components = {
        "slope": _slope_score(scene["slope"]),
        "vegetation": _vegetation_score(scene["ndvi"]),
        "landcover": _landcover_score(scene["landcover"]),
        "change": float(np.clip(100 - abs(np.nanmean(scene["ndvi"] - scene["historical_ndvi"])) * 300, 0, 100)),
    }
    score = float(sum(WEIGHTS[key] * value for key, value in components.items()))
    if score >= THRESHOLDS["green_min"]:
        label = "Green"
    elif score >= THRESHOLDS["yellow_min"]:
        label = "Yellow"
    else:
        label = "Red"
    reasons = []
    if components["slope"] < 60:
        reasons.append("Steeper terrain lowers the current suitability component.")
    if components["vegetation"] < 60:
        reasons.append("Higher vegetation density increases environmental sensitivity.")
    if components["landcover"] < 50:
        reasons.append("Observed land-cover classes include areas with stronger constraints.")
    if components["change"] < 80:
        reasons.append("The current and historical NDVI surfaces show a measurable difference.")
    if not reasons:
        reasons.append("The indicators show relatively lower constraints in this demo scene.")
    return Assessment(score, label, tuple(reasons), components)