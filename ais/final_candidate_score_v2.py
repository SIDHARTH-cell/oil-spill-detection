import pandas as pd
import numpy as np
from math import exp, radians, sin, cos, sqrt, atan2


# ============================================================
# FILES
# ============================================================

TRAJECTORY_FILE = "outputs/candidate_vessels.csv"
SOURCE_FILE = "outputs/source_uncertainty.csv"

OUTPUT_FILE = "outputs/final_candidate_ranking_v2.csv"


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
# LOAD
# ============================================================

trajectory = pd.read_csv(
    TRAJECTORY_FILE
)

sources = pd.read_csv(
    SOURCE_FILE
)


# ============================================================
# SOURCE DISTRIBUTION
# ============================================================

source_lat = sources["latitude"].values
source_lon = sources["longitude"].values


# ============================================================
# SOURCE REGION DISTANCE
# ============================================================

def source_region_distance(vessel_lat, vessel_lon):

    distances = []

    for lat, lon in zip(
        source_lat,
        source_lon
    ):

        distances.append(
            haversine_km(
                vessel_lat,
                vessel_lon,
                lat,
                lon
            )
        )

    distances = np.array(
        distances
    )

    return distances.min()


# ============================================================
# SCORE FUNCTIONS
# ============================================================

def distance_score(distance):

    if pd.isna(distance):
        return 0.0

    return exp(
        -distance / 20.0
    )


def approach_score(distance_change):

    if pd.isna(distance_change):
        return 0.0

    if distance_change <= 0:
        return 0.0

    return min(
        distance_change / 20.0,
        1.0
    )


def heading_score(difference):

    if pd.isna(difference):
        return 0.0

    if difference >= 90:
        return 0.0

    return 1.0 - (
        difference / 90.0
    )


def time_score(hours):

    if pd.isna(hours):
        return 0.0

    if hours < 0:
        return 0.0

    return exp(
        -hours / 4.0
    )


# ============================================================
# CALCULATE SOURCE-REGION DISTANCE
# ============================================================

trajectory[
    "source_region_distance_km"
] = trajectory.apply(
    lambda row:
        source_region_distance(
            row["last_latitude"],
            row["last_longitude"]
        ),
    axis=1
)


# ============================================================
# COMPONENT SCORES
# ============================================================

trajectory[
    "trajectory_distance_score"
] = trajectory[
    "closest_distance_km"
].apply(
    distance_score
)


trajectory[
    "approach_score"
] = trajectory[
    "distance_change_km"
].apply(
    approach_score
)


trajectory[
    "heading_score"
] = trajectory[
    "heading_difference"
].apply(
    heading_score
)


trajectory[
    "time_score"
] = trajectory[
    "hours_before_spill"
].apply(
    time_score
)


trajectory[
    "source_region_score"
] = trajectory[
    "source_region_distance_km"
].apply(
    distance_score
)


# ============================================================
# WEIGHTS
# ============================================================

W_TRAJECTORY_DISTANCE = 0.15
W_APPROACH = 0.15
W_HEADING = 0.15
W_TIME = 0.10

W_SOURCE_REGION = 0.45


# ============================================================
# FINAL SCORE
# ============================================================

trajectory[
    "final_score"
] = (

    W_TRAJECTORY_DISTANCE
    * trajectory[
        "trajectory_distance_score"
    ]

    +

    W_APPROACH
    * trajectory[
        "approach_score"
    ]

    +

    W_HEADING
    * trajectory[
        "heading_score"
    ]

    +

    W_TIME
    * trajectory[
        "time_score"
    ]

    +

    W_SOURCE_REGION
    * trajectory[
        "source_region_score"
    ]
)


trajectory[
    "priority_score"
] = (
    trajectory[
        "final_score"
    ] * 100
)


# ============================================================
# RANK
# ============================================================

trajectory = trajectory.sort_values(
    "final_score",
    ascending=False
).reset_index(drop=True)

trajectory[
    "rank"
] = trajectory.index + 1


# ============================================================
# DISPLAY
# ============================================================

print()
print("=" * 105)
print("FINAL SOURCE-REGION-AWARE CANDIDATE RANKING")
print("=" * 105)

print()

columns = [
    "rank",
    "mmsi",
    "vessel_name",
    "closest_distance_km",
    "distance_change_km",
    "heading_difference",
    "source_region_distance_km",
    "priority_score"
]

print(
    trajectory[
        columns
    ].to_string(
        index=False,
        float_format=lambda x:
            f"{x:.2f}"
    )
)


# ============================================================
# SAVE
# ============================================================

trajectory.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("Saved to:")
print(OUTPUT_FILE)