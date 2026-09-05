"""Anonymous Microsoft Planetary Computer STAC access for the live MVP path."""

from datetime import date

import numpy as np
import rasterio
from planetary_computer import sign
from pystac_client import Client
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
from rasterio.warp import transform_bounds

from indicators.ndvi import calculate_ndvi
from indicators.terrain import calculate_slope

CATALOG_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
REGION_BBOXES = {
    "Central Uttarakhand": (78.0, 29.5, 80.3, 31.3),
    "Garhwal": (77.8, 29.4, 79.6, 31.4),
    "Kumaon": (79.2, 29.4, 81.0, 30.9),
}

WORLDCOVER_LABELS = {
    10: "forest", 20: "grass-shrub", 30: "grass-shrub", 40: "agriculture",
    50: "built-up", 60: "bare", 70: "snow-ice", 80: "water", 90: "grass-shrub",
    95: "forest", 100: "grass-shrub",
}


def _read_clipped(asset_href: str, bbox: tuple[float, float, float, float], shape: tuple[int, int], resampling: Resampling) -> np.ndarray:
    """Read only a WGS84 bbox from a remote COG and resample to a common grid."""
    with rasterio.open(asset_href) as source:
        left, bottom, right, top = transform_bounds("EPSG:4326", source.crs, *bbox)
        window = rasterio.windows.from_bounds(left, bottom, right, top, source.transform)
        return source.read(1, window=window, out_shape=shape, resampling=resampling).astype(float)


def _search_one(catalog: Client, collection: str, bbox: tuple[float, float, float, float], datetime_range: str, query: dict | None = None):
    search = catalog.search(collections=[collection], bbox=bbox, datetime=datetime_range, query=query or {}, max_items=20)
    items = list(search.items())
    if not items:
        raise RuntimeError(f"No items found in the {collection} collection for this region and date range.")
    return sorted(items, key=lambda item: item.properties.get("eo:cloud_cover", 0))[0]


def load_live_scene(region: str, start_date: date, end_date: date) -> dict[str, object]:
    """Fetch a compact, clipped multi-source scene from free public STAC assets."""
    if start_date > end_date:
        raise ValueError("The start date must be before the end date.")
    bbox = REGION_BBOXES[region]
    catalog = Client.open(CATALOG_URL)
    datetime_range = f"{start_date.isoformat()}T00:00:00Z/{end_date.isoformat()}T23:59:59Z"
    sentinel = _search_one(catalog, "sentinel-2-l2a", bbox, datetime_range, {"eo:cloud_cover": {"lt": 60}})
    signed_assets = {name: sign(asset).href for name, asset in sentinel.assets.items()}
    output_shape = (80, 100)
    red = _read_clipped(signed_assets["B04"], bbox, output_shape, Resampling.bilinear) / 10000
    nir = _read_clipped(signed_assets["B08"], bbox, output_shape, Resampling.bilinear) / 10000
    scl = _read_clipped(signed_assets["SCL"], bbox, output_shape, Resampling.nearest)
    valid = ~np.isin(scl, [0, 3, 8, 9, 10, 11])
    ndvi = np.where(valid, calculate_ndvi(red, nir), np.nan)

    dem_item = _search_one(catalog, "cop-dem-glo-30", bbox, "2020-01-01T00:00:00Z/2026-12-31T23:59:59Z")
    dem_asset = dem_item.assets.get("data") or next(iter(dem_item.assets.values()))
    elevation = _read_clipped(sign(dem_asset).href, bbox, output_shape, Resampling.bilinear)
    slope = calculate_slope(elevation, cell_size=30)

    worldcover_item = _search_one(catalog, "esa-worldcover", bbox, "2020-01-01T00:00:00Z/2022-12-31T23:59:59Z")
    worldcover_asset = worldcover_item.assets.get("map") or next(iter(worldcover_item.assets.values()))
    landcover_code = _read_clipped(sign(worldcover_asset).href, bbox, output_shape, Resampling.nearest).astype(int)
    landcover = np.vectorize(lambda code: WORLDCOVER_LABELS.get(int(code), "bare"))(landcover_code)
    historical_ndvi = ndvi.copy()
    latitudes, longitudes = np.meshgrid(np.linspace(bbox[1], bbox[3], output_shape[0]), np.linspace(bbox[0], bbox[2], output_shape[1]), indexing="ij")
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
        "suitability": np.clip(100 - slope * 2.2, 0, 100),
        "data_source": "Microsoft Planetary Computer STAC: Sentinel-2 L2A, Copernicus DEM GLO-30, ESA WorldCover",
        "scene_id": sentinel.id,
        "scene_datetime": sentinel.datetime.isoformat() if sentinel.datetime else "unknown",
        "cloud_cover": sentinel.properties.get("eo:cloud_cover"),
    }