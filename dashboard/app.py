import streamlit as st
import pandas as pd
import json
from shapely.geometry import shape
import sys
from pathlib import Path
import streamlit as st
import torch
import numpy as np
import rasterio

from PIL import Image


# Project root
ROOT = Path(__file__).resolve().parent.parent

OUTPUTS = ROOT / "outputs"
AIS = ROOT / "ais"
MODEL_PATH = ROOT / "best_unet.pth"


# Allow Python to find models/unet.py
sys.path.append(str(ROOT))

from models.unet import UNet
@st.cache_resource
def load_unet():

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = UNet(
        in_channels=3,
        out_channels=1
    )

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=device
    )

    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        checkpoint = checkpoint["model_state_dict"]

    model.load_state_dict(checkpoint)

    model.to(device)
    model.eval()

    return model, device

# --------------------------------------------------
# Page setup
# --------------------------------------------------

st.set_page_config(
    page_title="Oil Spill Source Tracing",
    page_icon=None,
    layout="wide"
)

# --------------------------------------------------
# Simple styling
# --------------------------------------------------

st.markdown("""
<style>

.block-container {
    max-width: 1400px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* Hide heading anchor/link icons */
h1 a,
h2 a,
h3 a,
h4 a,
h5 a,
h6 a,
h1 button,
h2 button,
h3 button,
h4 button,
h5 button,
h6 button {
    display: none !important;
}

/* Main title */
h1 {
    font-size: 30px !important;
    font-weight: 600 !important;
    letter-spacing: -0.3px;
    margin-bottom: 2px !important;
}

/* Section headings */
h2 {
    font-size: 21px !important;
    font-weight: 600 !important;
    margin-top: 32px !important;
    margin-bottom: 6px !important;
}

h3 {
    font-size: 17px !important;
    font-weight: 600 !important;
}

/* Subtitle */
.subtitle {
    color: #A7A7A7;
    font-size: 14px;
    margin-bottom: 20px;
}

/* Small labels */
.info-label {
    color: #A7A7A7;
    font-size: 12px;
    margin-bottom: 3px;
}

/* Information values */
.info-value {
    color: #E6E6E6;
    font-size: 15px;
    font-weight: 500;
}

/* Section separator */
.section-line {
    border-top: 1px solid #dddddd;
    margin-top: 5px;
    margin-bottom: 20px;
}

/* Reduce excessive Streamlit spacing */
div[data-testid="stVerticalBlock"] {
    gap: 0.65rem;
}

/* Tables */
div[data-testid="stDataFrame"] {
    border: 1px solid #dddddd;
    border-radius: 4px;
}

/* Footer */
.footer {
    color: #888888;
    font-size: 12px;
    margin-top: 40px;
    padding-top: 15px;
    border-top: 1px solid #dddddd;
}

</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Paths
# --------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent

OUTPUTS = ROOT / "outputs"
AIS = ROOT / "ais"

# --------------------------------------------------
# Header
# --------------------------------------------------

st.title("Oil Spill Source Tracing")

st.markdown(
    '<div class="subtitle">'
    'Sentinel-1 detection and vessel trajectory analysis'
    '</div>',
    unsafe_allow_html=True
)

# --------------------------------------------------
# Data note
# --------------------------------------------------

st.caption(
    "Demonstration system. AIS and environmental data are synthetic."
)

# --------------------------------------------------
# Spill information
# --------------------------------------------------

st.header("Spill Information")

st.markdown('<div class="section-line"></div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('<div class="info-label">Date</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="info-value">27 July 2020</div>',
        unsafe_allow_html=True
    )

with col2:
    st.markdown('<div class="info-label">Time</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="info-value">00:15:46 UTC</div>',
        unsafe_allow_html=True
    )

with col3:
    st.markdown('<div class="info-label">Location</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="info-value">19.6881° N, 92.0788° W</div>',
        unsafe_allow_html=True
    )

with col4:
    st.markdown('<div class="info-label">Sensor</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="info-value">Sentinel-1</div>',
        unsafe_allow_html=True
    )

# --------------------------------------------------
# Geographic map
# --------------------------------------------------

import plotly.graph_objects as go

st.header("Geographic View")

st.markdown(
    '<div class="section-line"></div>',
    unsafe_allow_html=True
)

# Spill location
spill_lat = 19.68805
spill_lon = -92.07878

fig = go.Figure()

# --------------------------------------------------
# Vessel tracks
# --------------------------------------------------

ais_file = AIS / "synthetic_ais.csv"

ranking_file = OUTPUTS / "final_candidate_ranking_v2.csv"

selected_vessel = None

if ranking_file.exists():

    ranking = pd.read_csv(ranking_file)

    if len(ranking) > 0 and "vessel_name" in ranking.columns:
        selected_vessel = str(ranking.iloc[0]["vessel_name"])


# Simple muted vessel colors
vessel_colors = [
    "#4C78A8",
    "#72B7B2",
    "#F2A65A",
    "#8E9AAF",
    "#6C8E7B",
    "#B07AA1",
    "#7F8C8D",
    "#C17C74"
]


if ais_file.exists():

    ais = pd.read_csv(ais_file)

    for index, (mmsi, vessel) in enumerate(ais.groupby("mmsi")):

        vessel_name = str(vessel["vessel_name"].iloc[0])

        is_selected = (
            selected_vessel is not None
            and vessel_name == selected_vessel
        )

        # Give each vessel its own muted color
        vessel_color = vessel_colors[
            index % len(vessel_colors)
        ]

        # Make selected candidate more prominent
        if is_selected:
            line_width = 4
            opacity = 1.0
            trace_name = f"{vessel_name} — selected candidate"
        else:
            line_width = 2
            opacity = 0.65
            trace_name = vessel_name

        fig.add_trace(
            go.Scattermap(
                lat=vessel["latitude"],
                lon=vessel["longitude"],
                mode="lines",
                name=trace_name,

                line=dict(
                    width=line_width,
                    color=vessel_color
                ),

                opacity=opacity,

                hovertemplate=(
                    "<b>%{fullData.name}</b><br>"
                    "Latitude: %{lat:.4f}<br>"
                    "Longitude: %{lon:.4f}"
                    "<extra></extra>"
                )
            )
        )
# --------------------------------------------------
# Detected spill polygon
# --------------------------------------------------

spill_geojson = OUTPUTS / "oil_spill_regions.geojson"

if spill_geojson.exists():

    with open(spill_geojson, "r", encoding="utf-8") as f:
        spill_data = json.load(f)

    features = spill_data.get("features", [])

    # Calculate approximate geographic area for every detected region
    regions = []

    for feature in features:

        geometry = feature.get("geometry")

        if geometry is None:
            continue

        try:
            polygon = shape(geometry)
            area = polygon.area

            regions.append(
                (area, geometry)
            )

        except Exception:
            continue

    # Sort largest → smallest
    regions.sort(
        key=lambda x: x[0],
        reverse=True
    )

    # Only display the largest detected region
    if regions:

        largest_geometry = regions[0][1]

        geometry_type = largest_geometry["type"]
        coordinates = largest_geometry["coordinates"]

        if geometry_type == "Polygon":

            rings = coordinates

        elif geometry_type == "MultiPolygon":

            rings = []

            for polygon in coordinates:
                rings.extend(polygon)

        else:

            rings = []

        for ring in rings:

            lons = [point[0] for point in ring]
            lats = [point[1] for point in ring]

            fig.add_trace(
                go.Scattermap(
                    lat=lats,
                    lon=lons,
                    mode="lines",
                    fill="toself",
                    fillcolor="rgba(180, 70, 70, 0.20)",
                    line=dict(width=2),
                    name="Detected spill",
                    hovertemplate=(
                        "<b>Detected spill region</b><br>"
                        "Latitude: %{lat:.5f}<br>"
                        "Longitude: %{lon:.5f}"
                        "<extra></extra>"
                    ),
                    showlegend=True
                )
            )
# --------------------------------------------------
# Spill centre
# --------------------------------------------------

fig.add_trace(
    go.Scattermap(
        lat=[spill_lat],
        lon=[spill_lon],
        mode="markers",
        name="Spill centre",
        marker=dict(size=10),
        hovertemplate=(
            "<b>Detected oil spill</b><br>"
            "Latitude: %{lat:.5f}<br>"
            "Longitude: %{lon:.5f}"
            "<extra></extra>"
        )
    )
)
# --------------------------------------------------
# Backward drift path
# --------------------------------------------------

drift_file = OUTPUTS / "backward_drift.csv"

if drift_file.exists():

    drift = pd.read_csv(drift_file)

    # Try to identify coordinate columns
    lat_column = next(
        (c for c in ["latitude", "lat", "source_lat"] if c in drift.columns),
        None
    )

    lon_column = next(
        (c for c in ["longitude", "lon", "source_lon"] if c in drift.columns),
        None
    )

    if lat_column and lon_column:

        drift = drift.dropna(
            subset=[lat_column, lon_column]
        )

        # Draw backward drift trajectory
        fig.add_trace(
            go.Scattermap(
                lat=drift[lat_column],
                lon=drift[lon_column],
                mode="lines",
                name="Backward drift",
                line=dict(
                    width=3,
                    color="#4C78A8"
                ),
                hovertemplate=(
                    "<b>Backward drift estimate</b><br>"
                    "Latitude: %{lat:.5f}<br>"
                    "Longitude: %{lon:.5f}"
                    "<extra></extra>"
                )
            )
        )

        # Estimated source = final point of backward trajectory
        source_lat = drift[lat_column].iloc[-1]
        source_lon = drift[lon_column].iloc[-1]

        fig.add_trace(
            go.Scattermap(
                lat=[source_lat],
                lon=[source_lon],
                mode="markers",
                name="Estimated source",
                marker=dict(
                    size=11
                ),
                hovertemplate=(
                    "<b>Estimated source</b><br>"
                    "Latitude: %{lat:.5f}<br>"
                    "Longitude: %{lon:.5f}"
                    "<extra></extra>"
                )
            )
        )

# --------------------------------------------------
# Source uncertainty region
# --------------------------------------------------

uncertainty_file = OUTPUTS / "source_uncertainty.csv"

if uncertainty_file.exists():

    uncertainty = pd.read_csv(uncertainty_file)

    lat_column = next(
        (
            c for c in ["latitude", "lat", "source_lat"]
            if c in uncertainty.columns
        ),
        None
    )

    lon_column = next(
        (
            c for c in ["longitude", "lon", "source_lon"]
            if c in uncertainty.columns
        ),
        None
    )

    if lat_column and lon_column:

        uncertainty = uncertainty.dropna(
            subset=[lat_column, lon_column]
        )

        # Calculate approximate bounding region
        min_lat = uncertainty[lat_column].quantile(0.025)
        max_lat = uncertainty[lat_column].quantile(0.975)

        min_lon = uncertainty[lon_column].quantile(0.025)
        max_lon = uncertainty[lon_column].quantile(0.975)

        # Draw an approximate 95% source region
        region_lat = [
            min_lat,
            min_lat,
            max_lat,
            max_lat,
            min_lat
        ]

        region_lon = [
            min_lon,
            max_lon,
            max_lon,
            min_lon,
            min_lon
        ]

        fig.add_trace(
            go.Scattermap(
                lat=region_lat,
                lon=region_lon,
                mode="lines",
                name="Approx. source region",
                line=dict(
                    width=2,
                    color="#6B7280"
                ),
                fill="toself",
                fillcolor="rgba(80, 100, 120, 0.10)",
                hoverinfo="skip"
            )
        )

        # Plot individual simulation points very lightly
        fig.add_trace(
            go.Scattermap(
                lat=uncertainty[lat_column],
                lon=uncertainty[lon_column],
                mode="markers",
                name="Drift simulations",
                marker=dict(
                    size=3,
                    opacity=0.15
                ),
                hovertemplate=(
                    "<b>Simulated source</b><br>"
                    "Latitude: %{lat:.5f}<br>"
                    "Longitude: %{lon:.5f}"
                    "<extra></extra>"
                )
            )
        )
# --------------------------------------------------
# Map layout
# --------------------------------------------------

fig.update_layout(
    map=dict(
        style="open-street-map",
        center=dict(
            lat=spill_lat,
            lon=spill_lon
        ),
        zoom=12
    ),
    height=600,
    margin=dict(
        l=0,
        r=0,
        t=10,
        b=10
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=0.01,
        xanchor="left",
        x=0.01
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)
# --------------------------------------------------
# Selected vessel analysis
# --------------------------------------------------

st.header("Selected Vessel")

st.markdown(
    '<div class="section-line"></div>',
    unsafe_allow_html=True
)

ranking_file = OUTPUTS / "final_candidate_ranking_v2.csv"

if ranking_file.exists():

    ranking = pd.read_csv(ranking_file)

    if len(ranking) > 0:

        # Highest-ranked vessel
        candidate = ranking.iloc[0]

        vessel_name = str(candidate["vessel_name"])

        st.subheader(vessel_name)

        st.caption(
            "Highest-priority candidate based on trajectory "
            "and source-region compatibility."
        )

        # ------------------------------------------
        # Main measurements
        # ------------------------------------------

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Closest distance",
                f"{candidate['closest_distance_km']:.2f} km"
            )

        with col2:
            st.metric(
                "Approach distance",
                f"{candidate['distance_change_km']:.2f} km"
            )

        with col3:
            st.metric(
                "Source-region distance",
                f"{candidate['source_region_distance_km']:.2f} km"
            )

        with col4:
            st.metric(
                "Priority index",
                f"{candidate['priority_score']:.2f}"
            )

        # ------------------------------------------
        # Evidence
        # ------------------------------------------

        st.subheader("Evidence")

        evidence = pd.DataFrame({
            "Measure": [
                "Closest distance to spill",
                "Distance one hour earlier",
                "Distance change",
                "Moving toward spill",
                "Bearing to spill",
                "Vessel course",
                "Heading difference",
                "Heading compatible",
                "Average speed",
                "Time before spill",
                "Source-region distance"
            ],

            "Value": [
                f"{candidate['closest_distance_km']:.2f} km",
                f"{candidate['previous_distance_km']:.2f} km",
                f"{candidate['distance_change_km']:.2f} km",
                str(candidate['moving_toward_spill']),
                f"{candidate['bearing_to_spill']:.2f}°",
                f"{candidate['vessel_course']:.2f}°",
                f"{candidate['heading_difference']:.2f}°",
                str(candidate['heading_compatible']),
                f"{candidate['average_speed_knots']:.2f} knots",
                f"{candidate['hours_before_spill']:.2f} hours",
                f"{candidate['source_region_distance_km']:.2f} km"
            ]
        })

        st.dataframe(
            evidence,
            use_container_width=True,
            hide_index=True
        )

        # ------------------------------------------
        # Score breakdown
        # ------------------------------------------

        st.subheader("Priority Score Breakdown")

        score_breakdown = pd.DataFrame({
            "Component": [
                "Trajectory distance",
                "Approach",
                "Heading",
                "Time",
                "Source region"
            ],

            "Score": [
                candidate["trajectory_distance_score"],
                candidate["approach_score"],
                candidate["heading_score"],
                candidate["time_score"],
                candidate["source_region_score"]
            ]
        })

        st.dataframe(
            score_breakdown,
            use_container_width=True,
            hide_index=True
        )

        # ------------------------------------------
        # Interpretation
        # ------------------------------------------

        st.subheader("Interpretation")

        st.write(
            f"{vessel_name} is currently the highest-priority "
            "candidate because its previous trajectory and position "
            "are relatively compatible with the estimated source region."
        )

        st.caption(
            "The priority index is a prototype compatibility score, "
            "not a probability of responsibility."
        )

    else:

        st.warning(
            "The candidate ranking file is empty."
        )

else:

    st.warning(
        "Candidate ranking file was not found."
    )
# --------------------------------------------------
# Candidate vessel analysis
# --------------------------------------------------

st.header("Candidate Vessel Analysis")

st.markdown(
    '<div class="section-line"></div>',
    unsafe_allow_html=True
)

ranking_file = OUTPUTS / "final_candidate_ranking_v2.csv"

if ranking_file.exists():

    ranking = pd.read_csv(ranking_file)

    # Columns we actually want people to see
    display_columns = [
        "rank",
        "vessel_name",
        "vessel_type",
        "closest_distance_km",
        "distance_change_km",
        "heading_compatible",
        "source_region_distance_km",
        "priority_score"
    ]

    available_columns = [
        column
        for column in display_columns
        if column in ranking.columns
    ]

    table = ranking[available_columns].copy()

    # Friendly names
    table = table.rename(columns={
        "rank": "Rank",
        "vessel_name": "Vessel",
        "vessel_type": "Type",
        "closest_distance_km": "Distance to spill (km)",
        "distance_change_km": "Approach distance (km)",
        "heading_compatible": "Heading compatible",
        "source_region_distance_km": "Source distance (km)",
        "priority_score": "Priority index"
    })

    # Round numeric columns
    numeric_columns = [
        "Distance to spill (km)",
        "Approach distance (km)",
        "Source distance (km)",
        "Priority index"
    ]

    for column in numeric_columns:

        if column in table.columns:
            table[column] = table[column].round(2)

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Candidates are ordered by the prototype priority index. "
        "The index represents compatibility with the available "
        "trajectory and source-tracing evidence."
    )

else:

    st.warning(
        "Candidate ranking file was not found."
    )


# --------------------------------------------------
# Data and method
# --------------------------------------------------

st.header("Data and Method")

st.markdown(
    '<div class="section-line"></div>',
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)

with col1:

    st.write("**Satellite data**")
    st.write("Sentinel-1 SAR imagery")

    st.write("**Segmentation model**")
    st.write("U-Net")

    st.write("**Vessel data**")
    st.write("Synthetic AIS demonstration data")

with col2:

    st.write("**Environmental data**")
    st.write("Synthetic current and wind conditions")

    st.write("**Source estimation**")
    st.write("Backward drift modelling")

    st.write("**Uncertainty analysis**")
    st.write("Monte Carlo drift simulations")


# --------------------------------------------------
# Footer
# --------------------------------------------------

st.markdown(
    '<div class="footer">'
    'Oil Spill Source Tracing — prototype decision-support system'
    '</div>',
    unsafe_allow_html=True
)