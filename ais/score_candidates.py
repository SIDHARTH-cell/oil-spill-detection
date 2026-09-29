import pandas as pd
import numpy as np
from math import exp


# ============================================================
# FILES
# ============================================================

INPUT_FILE = "outputs/candidate_vessels.csv"
OUTPUT_FILE = "outputs/scored_candidates.csv"


# ============================================================
# SCORE FUNCTIONS
# ============================================================

def distance_score(distance_km):
    """
    Closer vessel -> higher spatial compatibility.
    """

    if pd.isna(distance_km):
        return 0.0

    return exp(-distance_km / 20.0)


def heading_score(heading_difference):
    """
    Smaller difference between vessel course and the
    bearing toward the spill -> higher compatibility.
    """

    if pd.isna(heading_difference):
        return 0.0

    if heading_difference >= 90:
        return 0.0

    return 1.0 - (
        heading_difference / 90.0
    )


def time_score(hours_before_spill):
    """
    For this first prototype, positions closer to the
    spill detection time receive a higher score.
    """

    if pd.isna(hours_before_spill):
        return 0.0

    if hours_before_spill < 0:
        return 0.0

    return exp(
        -hours_before_spill / 4.0
    )


def approach_score(distance_change_km):
    """
    Positive distance change means the vessel moved
    closer to the spill during the previous hour.
    """

    if pd.isna(distance_change_km):
        return 0.0

    if distance_change_km <= 0:
        return 0.0

    # 20 km/hour or more = maximum approach score
    return min(
        distance_change_km / 20.0,
        1.0
    )


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(INPUT_FILE)

print("Candidates loaded:", len(df))


# ============================================================
# REQUIRED COLUMNS
# ============================================================

required_columns = [
    "mmsi",
    "vessel_name",
    "closest_distance_km",
    "heading_difference",
    "hours_before_spill",
    "moving_toward_spill"
]

missing = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing:

    print()
    print("ERROR: Missing columns:")
    print(missing)

    print()
    print("Available columns:")
    print(df.columns.tolist())

    raise SystemExit(1)


# ============================================================
# CALCULATE COMPONENT SCORES
# ============================================================

df["distance_score"] = (
    df["closest_distance_km"]
    .apply(distance_score)
)

df["heading_score"] = (
    df["heading_difference"]
    .apply(heading_score)
)

df["time_score"] = (
    df["hours_before_spill"]
    .apply(time_score)
)

df["approach_score"] = (
    df["distance_change_km"]
    .apply(approach_score)
)


# ============================================================
# WEIGHTS
# ============================================================

W_DISTANCE = 0.35
W_APPROACH = 0.25
W_HEADING = 0.25
W_TIME = 0.15


# ============================================================
# FINAL COMPATIBILITY SCORE
# ============================================================

df["compatibility_score"] = (

    W_DISTANCE * df["distance_score"]

    +

    W_APPROACH * df["approach_score"]

    +

    W_HEADING * df["heading_score"]

    +

    W_TIME * df["time_score"]
)


# Convert to 0-100 presentation scale

df["compatibility_score_100"] = (
    df["compatibility_score"] * 100
)


# ============================================================
# SORT
# ============================================================

df = df.sort_values(
    "compatibility_score",
    ascending=False
).reset_index(drop=True)


df["rank"] = (
    df.index + 1
)


# ============================================================
# DISPLAY
# ============================================================

print()
print("=" * 90)
print("AIS CANDIDATE COMPATIBILITY")
print("=" * 90)
print()

columns = [
    "rank",
    "mmsi",
    "vessel_name",
    "closest_distance_km",
    "hours_before_spill",
    "heading_difference",
    "distance_score",
    "approach_score",
    "heading_score",
    "time_score",
    "compatibility_score_100"
]

print(
    df[columns].to_string(
        index=False,
        float_format=lambda x: f"{x:.3f}"
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
print("Results saved to:")
print(OUTPUT_FILE)