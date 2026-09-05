# HimalayaLens

HimalayaLens is a Python-first Streamlit decision-support application for exploring satellite-derived environmental indicators across Uttarakhand. It follows:

**Observe -> Measure -> Compare -> Assess -> Explain**

The app supports two modes: deterministic local demo fixtures for offline development, and a live public-data path using free, anonymous STAC assets. It does not use Google Earth Engine, paid APIs, or credentials.

## Run locally

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Run the pure calculation tests with:

```powershell
python -m pytest
```

## Architecture

- `providers/` will own public Sentinel-2, DEM, land-cover, and boundary access.
- `preprocessing/` will clip, mask, align, reproject, and normalize data.
- `indicators/` contains measurements such as NDVI and slope.
- `models/` contains scoring, thresholds, and explanations independent of the UI.
- `app.py` orchestrates inputs, cached data, model execution, and presentation.

Large satellite datasets should remain remote or cached locally and must not be committed to Git.

## Data sources

Selecting **Live public data** in the sidebar queries the Microsoft Planetary Computer STAC API at `https://planetarycomputer.microsoft.com/api/stac/v1`:

- **Sentinel-2 Level-2A (`sentinel-2-l2a`)**: B04 red and B08 near-infrared bands for NDVI, plus SCL for cloud, shadow, snow, and invalid-pixel masking. The provider selects the lowest-cloud scene in the requested window, subject to a 60% cloud-cover filter.
- **Copernicus DEM GLO-30 (`cop-dem-glo-30`)**: elevation and derived slope.
- **ESA WorldCover (`esa-worldcover`)**: categorical land-cover classes mapped into readable groups such as forest, agriculture, built-up, water, bare, and snow-ice.

The provider clips and resamples remote Cloud Optimized GeoTIFF assets to a compact common display grid. The app shows the Sentinel-2 item ID, acquisition timestamp, cloud cover, and provider name under **Methodology and data provenance**. The live result is cached with Streamlit for one day.

The current live slice is a current-observation MVP: historical NDVI comparison is not yet a second Sentinel-2 acquisition, so the provider currently mirrors the current NDVI for that field. A subsequent change-detection slice should query a separate historical window and record both item IDs.

If a public request fails because of connectivity, no matching imagery, provider changes, or missing local geospatial dependencies, the app reports the failure and uses a clearly labeled demo fallback. It never silently presents demo values as satellite observations.

## Method and limitations

NDVI is calculated as `(NIR - RED) / (NIR + RED)`. Terrain slope is derived from an elevation surface. The initial suitability score is a provisional weighted rule-based model, not AI. Its weights and thresholds require published guidance, empirical validation, and sensitivity analysis.

Satellite observations can be affected by clouds, shadows, haze, snow, seasonality, terrain effects, spatial resolution, and classification errors. The output is environmental planning support only. It is not legal construction approval, professional engineering or geotechnical assessment, or a guaranteed landslide or flood prediction.

## Live-data dependencies

The live provider uses `pystac-client`, `planetary-computer`, and `rasterio`. Confirm that the selected VS Code Python interpreter can import all three packages before selecting Live public data. The offline tests do not require a network connection or a live provider response.