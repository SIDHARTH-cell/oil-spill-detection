import pandas as pd
import numpy as np
from math import radians, sin, cos


# ============================================================
# INPUT
# ============================================================

ENVIRONMENT_FILE = "ais/synthetic_environment.csv"

SPILL_LAT = 19.68805
SPILL_LON = -92.07878

SPILL_TIME = pd.Timestamp(
    "2020-07-27 00:15:46",
    tz="UTC"
)


# ============================================================
# MODEL PARAMETERS
# ============================================================

# How far backward we simulate
BACKWARD_HOURS = 2.0

# Time step
STEP_MINUTES = 10

# Fraction of wind speed transferred to the oil.
#
# This is deliberately simplified for our demonstration.
WINDAGE = 0.02


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

env = pd.read_csv(
    ENVIRONMENT_FILE
)

env["timestamp"] = pd.to_datetime(
    env["timestamp"],
    utc=True
)

print("Environmental records:", len(env))


# ============================================================
# USE ENVIRONMENT AROUND SPILL
# ============================================================

env = env[
    env["timestamp"] <= SPILL_TIME
].copy()

env = env.sort_values(
    "timestamp"
)


# ============================================================
# BASIC VECTOR MOVEMENT
# ============================================================

def move_position(
    lat,
    lon,
    speed_knots,
    direction_deg,
    minutes
):
    """
    Move a position using a simple spherical approximation.

    direction_deg = direction the water/oil moves TOWARD.
    """

    distance_nm = (
        speed_knots
        * minutes
        / 60.0
    )

    distance_deg = (
        distance_nm / 60.0
    )

    direction = radians(
        direction_deg
    )

    dlat = (
        distance_deg
        * cos(direction)
    )

    dlon = (
        distance_deg
        * sin(direction)
        / cos(radians(lat))
    )

    return (
        lat + dlat,
        lon + dlon
    )


# ============================================================
# BACKWARD DRIFT
# ============================================================

lat = SPILL_LAT
lon = SPILL_LON

results = []

current_time = SPILL_TIME

steps = int(
    BACKWARD_HOURS
    * 60
    / STEP_MINUTES
)

print()
print("Starting backward drift...")
print(
    f"Starting position: "
    f"{lat:.6f}, {lon:.6f}"
)

for step in range(steps + 1):

    # --------------------------------------------------------
    # Find closest environmental record
    # --------------------------------------------------------

    differences = abs(
        env["timestamp"]
        - current_time
    )

    nearest_idx = differences.idxmin()

    environment = env.loc[
        nearest_idx
    ]

    # --------------------------------------------------------
    # Environmental values
    # --------------------------------------------------------

    current_speed = float(
        environment[
            "current_speed_knots"
        ]
    )

    current_direction = float(
        environment[
            "current_direction_deg"
        ]
    )

    wind_speed = float(
        environment[
            "wind_speed_knots"
        ]
    )

    wind_direction = float(
        environment[
            "wind_direction_deg"
        ]
    )

    # --------------------------------------------------------
    # Store current backward position
    # --------------------------------------------------------

    results.append({

        "time":
            current_time,

        "latitude":
            lat,

        "longitude":
            lon,

        "current_speed_knots":
            current_speed,

        "current_direction_deg":
            current_direction,

        "wind_speed_knots":
            wind_speed,

        "wind_direction_deg":
            wind_direction
    })

    # --------------------------------------------------------
    # Don't move after final point
    # --------------------------------------------------------

    if step == steps:
        break

    # --------------------------------------------------------
    # We are going BACKWARD.
    #
    # Therefore subtract the forward movement vector.
    # --------------------------------------------------------

    lat_current, lon_current = move_position(
        lat,
        lon,
        current_speed,
        current_direction,
        STEP_MINUTES
    )

    lat_wind, lon_wind = move_position(
        lat,
        lon,
        wind_speed * WINDAGE,
        wind_direction,
        STEP_MINUTES
    )

    # Forward displacement
    current_dlat = lat_current - lat
    current_dlon = lon_current - lon

    wind_dlat = lat_wind - lat
    wind_dlon = lon_wind - lon

    # Reverse it to go backward
    lat -= (
        current_dlat
        + wind_dlat
    )

    lon -= (
        current_dlon
        + wind_dlon
    )

    current_time -= pd.Timedelta(
        minutes=STEP_MINUTES
    )


# ============================================================
# RESULTS
# ============================================================

results_df = pd.DataFrame(
    results
)

output_file = (
    "outputs/backward_drift.csv"
)

results_df.to_csv(
    output_file,
    index=False
)


# ============================================================
# FINAL SOURCE ESTIMATE
# ============================================================

source = results_df.iloc[-1]

print()
print("=" * 65)
print("BACKWARD DRIFT RESULT")
print("=" * 65)

print()

print(
    "Detection position:"
)

print(
    f"  Latitude : {SPILL_LAT:.6f}"
)

print(
    f"  Longitude: {SPILL_LON:.6f}"
)

print()

print(
    "Estimated source region after "
    f"{BACKWARD_HOURS:.1f} hours:"
)

print(
    f"  Latitude : "
    f"{source['latitude']:.6f}"
)

print(
    f"  Longitude: "
    f"{source['longitude']:.6f}"
)

print()

print(
    "Saved trajectory:"
)

print(output_file)