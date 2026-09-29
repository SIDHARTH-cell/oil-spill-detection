import pandas as pd
import numpy as np
from math import exp


# ============================================================
# FILES
# ============================================================

TRAJECTORY_FILE = (
    "outputs/candidate_vessels.csv"
)

SOURCE_FILE = (
    "outputs/source_compatibility.csv"
)

OUTPUT_FILE = (
    "outputs/final_candidate_ranking.csv"
)


# ============================================================
# LOAD
# ============================================================

trajectory = pd.read_csv(
    TRAJECTORY_FILE
)

source = pd.read_csv(
    SOURCE_FILE
)


# ============================================================
# MERGE
# ============================================================

df = trajectory.merge(
    source[
        [
            "mmsi",
            "closest_source_distance_km",
            "source_time_difference_hours",
            "source_compatible"
        ]
    ],
    on="mmsi",
    how="left"
)


# ============================================================
# COMPONENT 1
# TRAJECTORY DISTANCE
# ============================================================

df["trajectory_distance_score"] = np.exp(
    -df["closest_distance_km"] / 20.0
)


# ============================================================
# COMPONENT 2
# APPROACH
# ============================================================

def calculate_approach_score(value):

    if pd.isna(value):
        return 0.0

    if value <= 0:
        return 0.0

    return min(
        value / 20.0,
        1.0
    )


df["approach_score"] = (
    df["distance_change_km"]
    .apply(calculate_approach_score)
)


# ============================================================
# COMPONENT 3
# HEADING
# ============================================================

def calculate_heading_score(value):

    if pd.isna(value):
        return 0.0

    if value >= 90:
        return 0.0

    return 1.0 - (
        value / 90.0
    )


df["heading_score"] = (
    df["heading_difference"]
    .apply(calculate_heading_score)
)


# ============================================================
# COMPONENT 4
# TIME
# ============================================================

def calculate_time_score(hours):

    if pd.isna(hours):
        return 0.0

    return exp(
        -abs(hours) / 4.0
    )


df["trajectory_time_score"] = (
    df["hours_before_spill"]
    .apply(calculate_time_score)
)


# ============================================================
# COMPONENT 5
# SOURCE DISTANCE
# ============================================================

df["source_distance_score"] = np.exp(
    -df["closest_source_distance_km"] / 20.0
)


# ============================================================
# COMPONENT 6
# SOURCE TIME
# ============================================================

df["source_time_score"] = (
    df[
        "source_time_difference_hours"
    ].apply(calculate_time_score)
)


# ============================================================
# FINAL WEIGHTS
# ============================================================

# These are demonstration weights.
# They are NOT calibrated probabilities.

W_TRAJECTORY_DISTANCE = 0.15
W_APPROACH = 0.15
W_HEADING = 0.15
W_TRAJECTORY_TIME = 0.10

W_SOURCE_DISTANCE = 0.30
W_SOURCE_TIME = 0.15


# ============================================================
# FINAL SCORE
# ============================================================

df["final_score"] = (

    W_TRAJECTORY_DISTANCE
    * df["trajectory_distance_score"]

    +

    W_APPROACH
    * df["approach_score"]

    +

    W_HEADING
    * df["heading_score"]

    +

    W_TRAJECTORY_TIME
    * df["trajectory_time_score"]

    +

    W_SOURCE_DISTANCE
    * df["source_distance_score"]

    +

    W_SOURCE_TIME
    * df["source_time_score"]
)


df["priority_score"] = (
    df["final_score"] * 100
)


# ============================================================
# RANK
# ============================================================

df = df.sort_values(
    "final_score",
    ascending=False
).reset_index(drop=True)

df["rank"] = (
    df.index + 1
)


# ============================================================
# DISPLAY
# ============================================================

print()
print("=" * 100)
print("FINAL OIL-SPILL SOURCE-TRACING CANDIDATES")
print("=" * 100)
print()

columns = [
    "rank",
    "mmsi",
    "vessel_name",
    "closest_distance_km",
    "distance_change_km",
    "heading_difference",
    "closest_source_distance_km",
    "source_time_difference_hours",
    "priority_score"
]

print(
    df[columns].to_string(
        index=False,
        float_format=lambda x: f"{x:.2f}"
    )
)


# ============================================================
# SAVE
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("Saved to:")
print(OUTPUT_FILE)