"""Provisional, explicit scoring configuration for the demo model."""

WEIGHTS = {
    "slope": 0.35,
    "vegetation": 0.25,
    "landcover": 0.25,
    "change": 0.15,
}

THRESHOLDS = {
    "green_min": 70.0,
    "yellow_min": 45.0,
}

LANDCOVER_SCORES = {
    "forest": 25.0,
    "agriculture": 55.0,
    "built-up": 35.0,
    "water": 5.0,
    "bare": 40.0,
    "grass-shrub": 70.0,
    "snow-ice": 10.0,
}