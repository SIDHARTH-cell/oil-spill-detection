import pandas as pd
import numpy as np
from math import radians, sin, cos, sqrt, atan2


# ============================================================
# FILES
# ============================================================

AIS_FILE = "ais/synthetic_ais.csv"
DRIFT_FILE = "outputs/backward_drift.csv"

OUTPUT_FILE = "outputs/source_compatibility.csv"


# ============================================================
# SPILL
# ============================================================

SPILL_TIME = pd.Timestamp(
    "2020-07-27 00:15:46",
    tz="UTC"
)


# ============================================================
# HAVERSINE
# ============================================================

def haversine_km(
    lat1,
    lon1,
    lat2,
    lon2
):

    R = 6371.0

    lat1 = radians(lat1)
    lat2 = radians(lat2)

    dlat = lat2 - lat1
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        +
        cos(lat1)
        * cos(lat2)
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return R * c


# ============================================================
# LOAD DATA
# ============================================================

ais = pd.read_csv(AIS_FILE)

ais["base_date_time"] = pd.to_datetime(
    ais["base_date_time"],
    utc=True
)

drift = pd.read_csv(DRIFT_FILE)

drift["time"] = pd.to_datetime(
    drift["time"],
    utc=True
)


# ============================================================
# SOURCE REGION
# ============================================================

source = drift.iloc[-1]

SOURCE_LAT = source["latitude"]
SOURCE_LON = source["longitude"]

SOURCE_TIME = source["time"]


print()
print("=" * 70)
print("ESTIMATED OIL SOURCE REGION")
print("=" * 70)

print(
    f"Latitude : {SOURCE_LAT:.6f}"
)

print(
    f"Longitude: {SOURCE_LON:.6f}"
)

print(
    f"Time     : {SOURCE_TIME}"
)


# ============================================================
# RELEVANT AIS WINDOW
# ============================================================

# We only need vessel positions before the spill
# and after the beginning of the backward-drift window.

earliest_time = drift["time"].min()

ais = ais[
    (ais["base_date_time"] >= earliest_time)
    &
    (ais["base_date_time"] < SPILL_TIME)
].copy()


# ============================================================
# CALCULATE SOURCE COMPATIBILITY
# ============================================================

results = []


for mmsi, vessel in ais.groupby("mmsi"):

    vessel = vessel.sort_values(
        "base_date_time"
    ).copy()


    # --------------------------------------------------------
    # Find closest vessel position to estimated source
    # --------------------------------------------------------

    distances = []

    for _, row in vessel.iterrows():

        distance = haversine_km(
            row["latitude"],
            row["longitude"],
            SOURCE_LAT,
            SOURCE_LON
        )

        distances.append(distance)


    vessel["source_distance_km"] = distances


    # --------------------------------------------------------
    # Closest approach
    # --------------------------------------------------------

    closest_idx = (
        vessel["source_distance_km"]
        .idxmin()
    )

    closest = vessel.loc[
        closest_idx
    ]


    closest_distance = (
        closest["source_distance_km"]
    )

    closest_time = (
        closest["base_date_time"]
    )


    # --------------------------------------------------------
    # Time difference between vessel and estimated source
    # --------------------------------------------------------

    time_difference_hours = abs(
        (
            closest_time
            - SOURCE_TIME
        ).total_seconds()
    ) / 3600


    # --------------------------------------------------------
    # Is vessel reasonably close to source?
    #
    # This is just a prototype threshold.
    # --------------------------------------------------------

    source_compatible = (
        closest_distance <= 15
        and
        time_difference_hours <= 2
    )


    # --------------------------------------------------------
    # Store
    # --------------------------------------------------------

    results.append({

        "mmsi":
            mmsi,

        "vessel_name":
            vessel["vessel_name"].iloc[0],

        "vessel_type":
            vessel["vessel_type"].iloc[0],

        "closest_source_distance_km":
            round(
                closest_distance,
                3
            ),

        "closest_source_time":
            closest_time,

        "source_time_difference_hours":
            round(
                time_difference_hours,
                3
            ),

        "source_compatible":
            source_compatible
    })


# ============================================================
# RESULTS
# ============================================================

results_df = pd.DataFrame(
    results
)

results_df = results_df.sort_values(
    "closest_source_distance_km"
)


# ============================================================
# DISPLAY
# ============================================================

print()
print("=" * 90)
print("VESSEL ↔ ESTIMATED SOURCE COMPATIBILITY")
print("=" * 90)

columns = [
    "mmsi",
    "vessel_name",
    "closest_source_distance_km",
    "source_time_difference_hours",
    "source_compatible"
]

print()

print(
    results_df[columns].to_string(
        index=False
    )
)


# ============================================================
# SAVE
# ============================================================

results_df.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("Saved to:")
print(OUTPUT_FILE)