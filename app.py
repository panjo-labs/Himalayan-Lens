"""Streamlit entry point for the HimalayaLens demo MVP."""

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from indicators.demo_data import build_demo_scene
from indicators.landcover import summarize_landcover
from models.explanations import explain_assessment
from models.scoring import assess_scene


LAYER_INFO = {
    "Suitability": {
        "key": "suitability",
        "description": "A provisional 0-100 planning-support score. Higher values mean fewer constraints in this demo model, not permission to build.",
        "range": "0-100",
        "scale": "RdYlGn",
        "task": "Construction screening: use as an early comparison layer, then check zoning, drainage, hazards, access, and site-specific engineering evidence.",
    },
    "NDVI": {
        "key": "ndvi",
        "description": "The Normalized Difference Vegetation Index. Higher values generally indicate denser or healthier green vegetation; low values may indicate bare ground, built-up land, water, or stressed vegetation.",
        "range": "-1 to 1",
        "scale": "YlGn",
        "task": "Vegetation monitoring: compare current and historical NDVI to locate vegetation decline, recovery, or seasonal differences.",
    },
    "Slope": {
        "key": "slope",
        "description": "Terrain steepness in degrees, derived from elevation. Steeper ground can increase planning constraints, but slope alone does not predict landslides.",
        "range": "0-90 degrees",
        "scale": "OrRd",
        "task": "Construction screening: identify steep areas for additional drainage, stability, access, and geotechnical review.",
    },
    "Elevation": {
        "key": "elevation",
        "description": "Approximate height above sea level in metres. Elevation helps provide terrain and climate context; it is not a direct suitability or hazard score.",
        "range": "metres above sea level",
        "scale": "Viridis",
        "task": "Terrain context: compare elevation bands when reviewing vegetation patterns, settlement conditions, and access constraints.",
    },
    "Land cover": {
        "key": "landcover_code",
        "description": "The dominant surface class in each grid cell. Forest, agriculture, grass-shrub, bare ground, and built-up areas imply different planning questions.",
        "range": "categorical classes",
        "scale": "Turbo",
        "task": "Land-cover change: use forest and agriculture locations as a starting point for conservation review, conversion checks, and field verification.",
    },
}


st.set_page_config(
    page_title="HimalayaLens",
    page_icon=":material/terrain:",
    layout="wide",
)


@st.cache_data
def load_demo_scene(region: str) -> dict[str, object]:
    """Load a small deterministic scene until live providers are connected."""
    return build_demo_scene(region)


@st.cache_data(ttl="1d", max_entries=10)
def load_live_data(region: str, start_date: date, end_date: date) -> dict[str, object]:
    """Load a clipped public-data scene and cache it across widget reruns."""
    from providers.planetary_computer import load_live_scene

    return load_live_scene(region, start_date, end_date)


def main() -> None:
    st.title("HimalayaLens")
    st.caption("Satellite-informed planning support for Uttarakhand")

    with st.sidebar:
        st.header("Analysis settings")
        data_mode = st.segmented_control("Data mode", ["Demo", "Live public data"], default="Demo")
        region = st.selectbox("Region", ["Central Uttarakhand", "Garhwal", "Kumaon"])
        date_range = st.date_input(
            "Observation window",
            value=(date(2023, 6, 1), date(2024, 6, 1)),
        )
        layer = st.selectbox("Map layer", ["Suitability", "NDVI", "Slope", "Elevation", "Land cover"])
        st.caption("Live mode queries anonymous public STAC assets and caches the clipped result locally.")

    if data_mode == "Live public data":
        try:
            scene = load_live_data(region, date_range[0], date_range[1])
        except Exception as error:
            st.error(f"Live data could not be loaded: {error}")
            st.info("Switch to Demo mode or expand the date range. No live-data result was used for this screen.")
            scene = load_demo_scene(f"{region} demo")
    else:
        scene = load_demo_scene(f"{region} demo")
    assessment = assess_scene(scene)
    landcover_summary = summarize_landcover(scene["landcover"])

    st.info("This is an evidence-based decision-support assessment, not legal approval, engineering advice, or a landslide prediction.")

    with st.container(horizontal=True):
        st.metric("Assessment", assessment.label, border=True)
        st.metric("Suitability score", f"{assessment.score:.0f} / 100", border=True)
        st.metric("Mean NDVI", f"{scene['ndvi'].mean():.2f}", border=True)
        st.metric("Mean slope", f"{scene['slope'].mean():.1f}°", border=True)

    left, right = st.columns([1.4, 1])
    with left:
        with st.container(border=True):
            st.subheader(f"{layer} map")
            layer_info = LAYER_INFO[layer]
            map_values = scene[layer_info["key"]]
            map_frame = pd.DataFrame(
                {
                    "lat": scene["latitudes"].ravel(),
                    "lon": scene["longitudes"].ravel(),
                    "value": map_values.ravel(),
                }
            )
            if layer == "Land cover":
                map_frame["label"] = map_frame["value"].map(
                    {1: "Forest", 2: "Agriculture", 3: "Grass-shrub", 4: "Bare", 5: "Built-up"}
                )
                figure = px.scatter_map(
                    map_frame,
                    lat="lat",
                    lon="lon",
                    color="label",
                    hover_data={"lat": ":.3f", "lon": ":.3f", "label": True},
                    zoom=6,
                    height=470,
                    color_discrete_sequence=px.colors.qualitative.Set2,
                )
            else:
                figure = px.scatter_map(
                    map_frame,
                    lat="lat",
                    lon="lon",
                    color="value",
                    color_continuous_scale=layer_info["scale"],
                    hover_data={"lat": ":.3f", "lon": ":.3f", "value": ":.2f"},
                    zoom=6,
                    height=470,
                )
            figure.update_traces(marker={"size": 13, "opacity": 0.78})
            figure.update_layout(
                map_style="open-street-map",
                margin={"l": 0, "r": 0, "t": 0, "b": 0},
                coloraxis_colorbar={"title": layer, "ticks": "outside"},
                legend={"title": {"text": "Land-cover class"}},
            )
            st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})
            st.caption(f"Displayed range: {layer_info['range']}. Values come from {'public clipped raster data' if data_mode == 'Live public data' else 'deterministic demo fixtures'}.")

    with right:
        with st.container(border=True):
            st.subheader("Why this area is flagged")
            st.write(explain_assessment(assessment, scene))
            for reason in assessment.reasons:
                st.markdown(f"- {reason}")

    with st.container(border=True):
        st.subheader(f"What {layer.lower()} means")
        st.write(LAYER_INFO[layer]["description"])
        st.markdown(f"**Useful task:** {LAYER_INFO[layer]['task']}")

    trend = pd.DataFrame(
        {
            "period": ["Historical", "Current"],
            "mean_ndvi": [scene["historical_ndvi"].mean(), scene["ndvi"].mean()],
        }
    ).set_index("period")
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader("Vegetation comparison")
            st.line_chart(trend, y="mean_ndvi")
    with col2:
        with st.container(border=True):
            st.subheader("Land-cover composition")
            st.bar_chart(landcover_summary)

    with st.expander("Methodology and data provenance"):
        source = scene.get("data_source", "Deterministic local demo fixtures")
        st.markdown(
            f"""
            **Current source:** {source}.

            **Live scene:** `{scene.get('scene_id', 'demo')}`; acquisition: `{scene.get('scene_datetime', 'local fixture')}`; cloud cover: `{scene.get('cloud_cover', 'not applicable')}`.

            **Indicators:** NDVI uses $\\frac{{NIR - RED}}{{NIR + RED}}$; slope is derived from an elevation surface; land cover is represented by interpretable classes.

            **Model:** a provisional, weighted rule-based score combines vegetation, slope, land cover, and change indicators. Weights and thresholds require published guidance, empirical validation, and sensitivity analysis before operational use.

            **Public access path:** Microsoft Planetary Computer STAC, using anonymous signed asset URLs. Google Earth Engine and paid services are not used.
            """
        )
        st.dataframe(
            pd.DataFrame(
                {
                    "Indicator": ["NDVI", "Elevation", "Slope", "Land cover", "Historical comparison"],
                    "Status": ["Demo", "Demo", "Demo", "Demo", "Demo"],
                    "Interpretation": ["Vegetation density", "Terrain context", "Development constraint", "Surface class", "Observed change signal"],
                }
            ),
            hide_index=True,
        )

    with st.expander("Suggested tasks"):
        st.markdown(
            """
            **Deforestation check**  
            Compare historical and current NDVI, inspect forest-class areas, and verify suspected loss with cloud-free imagery and field or authoritative reference data.

            **Construction screening**  
            Start with slope and suitability, then review land cover, drainage, access, protected areas, hazard references, local regulations, and professional site assessments.

            **Vegetation monitoring**  
            Compare NDVI across matching seasons. A persistent decline is a signal for investigation, not proof of deforestation by itself.

            **Land-cover change**  
            Track forest, agriculture, bare, and built-up class transitions between dates, while checking classification uncertainty and imagery quality.
            """
        )

    st.caption(f"Selected window: {date_range}. All outputs are indicative and depend on data quality, assumptions, weights, and thresholds.")


if __name__ == "__main__":
    main()