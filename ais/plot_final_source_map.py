import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


# ============================================================
# FILES
# ============================================================

AIS_FILE = "ais/synthetic_ais.csv"
SOURCE_FILE = "outputs/source_uncertainty.csv"


# ============================================================
# SPILL
# ============================================================

SPILL_LAT = 19.68805
SPILL_LON = -92.07878

SPILL_TIME = pd.Timestamp(
    "2020-07-27 00:15:46",
    tz="UTC"
)


# ============================================================
# LOAD DATA
# ============================================================

ais = pd.read_csv(AIS_FILE)

ais["base_date_time"] = pd.to_datetime(
    ais["base_date_time"],
    utc=True
)

sources = pd.read_csv(
    SOURCE_FILE
)


# ============================================================
# SOURCE STATISTICS
# ============================================================

latitudes = sources["latitude"]
longitudes = sources["longitude"]

lat_mean = latitudes.mean()
lon_mean = longitudes.mean()

lat_low = np.percentile(
    latitudes,
    2.5
)

lat_high = np.percentile(
    latitudes,
    97.5
)

lon_low = np.percentile(
    longitudes,
    2.5
)

lon_high = np.percentile(
    longitudes,
    97.5
)


# ============================================================
# CREATE FIGURE
# ============================================================

plt.figure(
    figsize=(13, 10)
)


# ============================================================
# BACKWARD-DRIFT SIMULATIONS
# ============================================================

plt.scatter(
    sources["longitude"],
    sources["latitude"],
    s=8,
    alpha=0.15,
    label="Backward-drift simulations"
)


# ============================================================
# 95% SOURCE REGION
# ============================================================

plt.plot(
    [
        lon_low,
        lon_high,
        lon_high,
        lon_low,
        lon_low
    ],
    [
        lat_low,
        lat_low,
        lat_high,
        lat_high,
        lat_low
    ],
    linestyle="--",
    linewidth=2,
    label="Approx. 95% source region"
)


# ============================================================
# VESSEL TRAJECTORIES
# ============================================================

for mmsi, vessel in ais.groupby("mmsi"):

    vessel = vessel.sort_values(
        "base_date_time"
    )

    name = vessel[
        "vessel_name"
    ].iloc[0]

    if str(mmsi) == "900000001":

        # Highlight planted source vessel
        plt.plot(
            vessel["longitude"],
            vessel["latitude"],
            linewidth=3,
            label=f"{name} — planted source"
        )

    else:

        plt.plot(
            vessel["longitude"],
            vessel["latitude"],
            linewidth=1,
            alpha=0.55,
            label=name
        )


# ============================================================
# DETECTED SPILL
# ============================================================

plt.scatter(
    SPILL_LON,
    SPILL_LAT,
    marker="*",
    s=350,
    label="Detected oil spill"
)


# ============================================================
# MEAN SOURCE
# ============================================================

plt.scatter(
    lon_mean,
    lat_mean,
    marker="X",
    s=200,
    label="Mean source estimate"
)


# ============================================================
# SOURCE TIME VESSEL POSITIONS
# ============================================================

# We want to see where each vessel was approximately
# around the beginning of the backward-drift period.

SOURCE_TIME = SPILL_TIME - pd.Timedelta(
    hours=2
)

TIME_WINDOW = pd.Timedelta(
    minutes=10
)

source_time_vessels = ais[
    abs(
        ais["base_date_time"]
        - SOURCE_TIME
    ) <= TIME_WINDOW
]


plt.scatter(
    source_time_vessels["longitude"],
    source_time_vessels["latitude"],
    marker="o",
    s=80,
    facecolors="none",
    linewidths=2,
    label="Vessel positions near source time"
)


# ============================================================
# LABEL IMPORTANT VESSELS
# ============================================================

for _, row in source_time_vessels.iterrows():

    if str(row["mmsi"]) == "900000001":

        plt.annotate(
            "OCEAN STAR",
            (
                row["longitude"],
                row["latitude"]
            ),
            xytext=(8, 8),
            textcoords="offset points"
        )


# ============================================================
# LABELS
# ============================================================

plt.xlabel(
    "Longitude"
)

plt.ylabel(
    "Latitude"
)

plt.title(
    "Oil Spill Source-Tracing: AIS + Backward Drift"
)

plt.grid(True)

plt.legend(
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.tight_layout()


# ============================================================
# SAVE
# ============================================================

OUTPUT_FILE = (
    "outputs/final_source_tracing_map.png"
)

plt.savefig(
    OUTPUT_FILE,
    dpi=250
)

print()
print(
    "Final source-tracing map saved to:"
)

print(
    OUTPUT_FILE
)

print()

print(
    "Estimated source center:"
)

print(
    f"Latitude : {lat_mean:.6f}"
)

print(
    f"Longitude: {lon_mean:.6f}"
)

print()

print(
    "Approximate 95% source region:"
)

print(
    f"Latitude : {lat_low:.6f} → {lat_high:.6f}"
)

print(
    f"Longitude: {lon_low:.6f} → {lon_high:.6f}"
)

plt.show()