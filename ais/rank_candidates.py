import pandas as pd
import numpy as np
from math import radians, sin, cos, sqrt, atan2, degrees


# ============================================================
# INPUT
# ============================================================

AIS_FILE = "ais/synthetic_ais.csv"

SPILL_LAT = 19.68805
SPILL_LON = -92.07878

SPILL_TIME = pd.Timestamp(
    "2020-07-27 00:15:46",
    tz="UTC"
)

LOOKBACK_HOURS = 8


# ============================================================
# HAVERSINE
# ============================================================

def haversine_km(lat1, lon1, lat2, lon2):

    R = 6371.0

    lat1 = radians(lat1)
    lat2 = radians(lat2)

    dlat = lat2 - lat1
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return R * c


# ============================================================
# BEARING
# ============================================================

def bearing_to_target(
    vessel_lat,
    vessel_lon,
    target_lat,
    target_lon
):

    lat1 = radians(vessel_lat)
    lat2 = radians(target_lat)

    dlon = radians(
        target_lon - vessel_lon
    )

    y = sin(dlon) * cos(lat2)

    x = (
        cos(lat1) * sin(lat2)
        -
        sin(lat1)
        * cos(lat2)
        * cos(dlon)
    )

    bearing = degrees(
        atan2(y, x)
    )

    return (bearing + 360) % 360


# ============================================================
# ANGLE DIFFERENCE
# ============================================================

def angle_difference(a, b):

    difference = abs(a - b)

    return min(
        difference,
        360 - difference
    )


# ============================================================
# LOAD
# ============================================================

df = pd.read_csv(AIS_FILE)

df["base_date_time"] = pd.to_datetime(
    df["base_date_time"],
    utc=True
)

print("Total AIS records:", len(df))
print("Total vessels:", df["mmsi"].nunique())


# ============================================================
# PRE-SPILL WINDOW
# ============================================================

lookback_start = (
    SPILL_TIME
    - pd.Timedelta(hours=LOOKBACK_HOURS)
)

df = df[
    (df["base_date_time"] >= lookback_start)
    &
    (df["base_date_time"] < SPILL_TIME)
].copy()

print(
    "Records inside pre-spill window:",
    len(df)
)


# ============================================================
# DISTANCE TO SPILL
# ============================================================

df["distance_km"] = df.apply(
    lambda row: haversine_km(
        row["latitude"],
        row["longitude"],
        SPILL_LAT,
        SPILL_LON
    ),
    axis=1
)


# ============================================================
# ANALYZE EACH VESSEL
# ============================================================

results = []


for mmsi, vessel in df.groupby("mmsi"):

    vessel = vessel.sort_values(
        "base_date_time"
    ).copy()


    # --------------------------------------------------------
    # LAST POSITION BEFORE SPILL
    # --------------------------------------------------------

    last = vessel.iloc[-1]

    last_lat = last["latitude"]
    last_lon = last["longitude"]

    last_time = last["base_date_time"]

    last_distance = last["distance_km"]


    # --------------------------------------------------------
    # TIME BEFORE SPILL
    # --------------------------------------------------------

    hours_before = (
        SPILL_TIME - last_time
    ).total_seconds() / 3600


    # --------------------------------------------------------
    # POSITION ONE HOUR EARLIER
    # --------------------------------------------------------

    one_hour_before = (
        last_time
        - pd.Timedelta(hours=1)
    )

    previous_points = vessel[
        vessel["base_date_time"]
        <= one_hour_before
    ]


    if len(previous_points) > 0:

        previous = previous_points.iloc[-1]

        previous_distance = previous[
            "distance_km"
        ]

        distance_change = (
            previous_distance
            - last_distance
        )

    else:

        previous_distance = np.nan
        distance_change = np.nan


    # --------------------------------------------------------
    # APPROACHING?
    # --------------------------------------------------------

    if pd.isna(distance_change):

        approaching = False

    else:

        approaching = (
            distance_change > 0
        )


    # --------------------------------------------------------
    # BEARING FROM LAST POSITION TO SPILL
    # --------------------------------------------------------

    bearing = bearing_to_target(
        last_lat,
        last_lon,
        SPILL_LAT,
        SPILL_LON
    )


    # --------------------------------------------------------
    # VESSEL COURSE
    # --------------------------------------------------------

    vessel_course = last["cog"]


    # --------------------------------------------------------
    # COURSE DIFFERENCE
    # --------------------------------------------------------

    heading_difference = angle_difference(
        vessel_course,
        bearing
    )


    # --------------------------------------------------------
    # HEADING COMPATIBILITY
    # --------------------------------------------------------

    heading_compatible = (
        heading_difference <= 45
    )


    # --------------------------------------------------------
    # AVERAGE SPEED
    # --------------------------------------------------------

    average_speed = vessel["sog"].mean()


    # --------------------------------------------------------
    # AIS POINTS
    # --------------------------------------------------------

    ais_points = len(vessel)


    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    results.append({

        "mmsi": mmsi,

        "vessel_name":
            vessel["vessel_name"].iloc[0],

        "vessel_type":
            vessel["vessel_type"].iloc[0],

        "last_latitude":
            last_lat,

        "last_longitude":
            last_lon,

        "last_ais_time":
            last_time,

        "closest_distance_km":
            round(last_distance, 3),

        "hours_before_spill":
            round(hours_before, 3),

        "previous_distance_km":
            round(previous_distance, 3)
            if not pd.isna(previous_distance)
            else np.nan,

        "distance_change_km":
            round(distance_change, 3)
            if not pd.isna(distance_change)
            else np.nan,

        "moving_toward_spill":
            approaching,

        "bearing_to_spill":
            round(bearing, 2),

        "vessel_course":
            round(vessel_course, 2),

        "heading_difference":
            round(heading_difference, 2),

        "heading_compatible":
            heading_compatible,

        "ais_points":
            ais_points,

        "average_speed_knots":
            round(average_speed, 2)
    })


# ============================================================
# SAVE
# ============================================================

results_df = pd.DataFrame(results)

results_df = results_df.sort_values(
    "closest_distance_km"
)

output_file = (
    "outputs/candidate_vessels.csv"
)

results_df.to_csv(
    output_file,
    index=False
)


# ============================================================
# DISPLAY
# ============================================================

print()
print("=" * 100)
print("PRE-SPILL VESSEL ANALYSIS")
print("=" * 100)
print()

columns = [
    "mmsi",
    "vessel_name",
    "closest_distance_km",
    "hours_before_spill",
    "distance_change_km",
    "bearing_to_spill",
    "vessel_course",
    "heading_difference",
    "moving_toward_spill"
]

print(
    results_df[columns].to_string(
        index=False
    )
)

print()
print("Saved to:")
print(output_file)