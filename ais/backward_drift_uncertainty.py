import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from math import radians, sin, cos, sqrt


# ============================================================
# INPUT
# ============================================================

ENVIRONMENT_FILE = (
    "ais/synthetic_environment.csv"
)

SPILL_LAT = 19.68805
SPILL_LON = -92.07878

SPILL_TIME = pd.Timestamp(
    "2020-07-27 00:15:46",
    tz="UTC"
)


# ============================================================
# MODEL
# ============================================================

BACKWARD_HOURS = 2.0

STEP_MINUTES = 10

N_SIMULATIONS = 500

# Mean fraction of wind speed transferred to oil
WINDAGE_MEAN = 0.02

# Uncertainty in windage
WINDAGE_STD = 0.005

# Environmental uncertainty
CURRENT_SPEED_STD = 0.08
CURRENT_DIRECTION_STD = 4.0

WIND_SPEED_STD = 1.0
WIND_DIRECTION_STD = 6.0


# ============================================================
# RANDOM SEED
# ============================================================

np.random.seed(42)


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

env = env.sort_values(
    "timestamp"
)


# ============================================================
# MOVEMENT
# ============================================================

def movement(
    lat,
    lon,
    speed_knots,
    direction_deg,
    minutes
):

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
        / max(
            cos(radians(lat)),
            0.01
        )
    )

    return (
        lat + dlat,
        lon + dlon
    )


# ============================================================
# ENVIRONMENT LOOKUP
# ============================================================

def get_environment(time):

    difference = abs(
        env["timestamp"] - time
    )

    index = difference.idxmin()

    return env.loc[index]


# ============================================================
# SIMULATION
# ============================================================

all_sources = []

steps = int(
    BACKWARD_HOURS
    * 60
    / STEP_MINUTES
)


for simulation in range(
    N_SIMULATIONS
):

    lat = SPILL_LAT
    lon = SPILL_LON

    current_time = SPILL_TIME

    # Random windage for this simulation
    windage = np.random.normal(
        WINDAGE_MEAN,
        WINDAGE_STD
    )

    windage = max(
        windage,
        0.0
    )

    for step in range(steps):

        environmental = (
            get_environment(
                current_time
            )
        )

        # ----------------------------------------------------
        # Add uncertainty
        # ----------------------------------------------------

        current_speed = (
            environmental[
                "current_speed_knots"
            ]
            +
            np.random.normal(
                0,
                CURRENT_SPEED_STD
            )
        )

        current_direction = (
            environmental[
                "current_direction_deg"
            ]
            +
            np.random.normal(
                0,
                CURRENT_DIRECTION_STD
            )
        )

        wind_speed = (
            environmental[
                "wind_speed_knots"
            ]
            +
            np.random.normal(
                0,
                WIND_SPEED_STD
            )
        )

        wind_direction = (
            environmental[
                "wind_direction_deg"
            ]
            +
            np.random.normal(
                0,
                WIND_DIRECTION_STD
            )
        )

        # Prevent negative speeds
        current_speed = max(
            current_speed,
            0
        )

        wind_speed = max(
            wind_speed,
            0
        )

        # ----------------------------------------------------
        # Forward displacement
        # ----------------------------------------------------

        current_lat, current_lon = movement(
            lat,
            lon,
            current_speed,
            current_direction,
            STEP_MINUTES
        )

        wind_lat, wind_lon = movement(
            lat,
            lon,
            wind_speed * windage,
            wind_direction,
            STEP_MINUTES
        )

        current_dlat = (
            current_lat - lat
        )

        current_dlon = (
            current_lon - lon
        )

        wind_dlat = (
            wind_lat - lat
        )

        wind_dlon = (
            wind_lon - lon
        )

        # ----------------------------------------------------
        # Reverse transport
        # ----------------------------------------------------

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

    all_sources.append({
        "simulation": simulation,
        "latitude": lat,
        "longitude": lon
    })


# ============================================================
# RESULTS
# ============================================================

sources = pd.DataFrame(
    all_sources
)

output_file = (
    "outputs/source_uncertainty.csv"
)

sources.to_csv(
    output_file,
    index=False
)


# ============================================================
# STATISTICS
# ============================================================

latitudes = sources[
    "latitude"
]

longitudes = sources[
    "longitude"
]


lat_mean = latitudes.mean()
lon_mean = longitudes.mean()

lat_std = latitudes.std()
lon_std = longitudes.std()

lat_95_low = np.percentile(
    latitudes,
    2.5
)

lat_95_high = np.percentile(
    latitudes,
    97.5
)

lon_95_low = np.percentile(
    longitudes,
    2.5
)

lon_95_high = np.percentile(
    longitudes,
    97.5
)


# ============================================================
# OUTPUT
# ============================================================

print()
print("=" * 70)
print("BACKWARD DRIFT UNCERTAINTY")
print("=" * 70)

print()

print(
    "Simulations:",
    N_SIMULATIONS
)

print()

print(
    "Mean estimated source:"
)

print(
    f"  Latitude : {lat_mean:.6f}"
)

print(
    f"  Longitude: {lon_mean:.6f}"
)

print()

print(
    "Standard deviation:"
)

print(
    f"  Latitude : {lat_std:.6f}"
)

print(
    f"  Longitude: {lon_std:.6f}"
)

print()

print(
    "Approximate 95% source region:"
)

print(
    f"  Latitude : "
    f"{lat_95_low:.6f} → {lat_95_high:.6f}"
)

print(
    f"  Longitude: "
    f"{lon_95_low:.6f} → {lon_95_high:.6f}"
)

print()

print(
    "Saved to:"
)

print(
    output_file
)


# ============================================================
# PLOT
# ============================================================

plt.figure(
    figsize=(10, 8)
)

plt.scatter(
    sources["longitude"],
    sources["latitude"],
    s=8,
    alpha=0.25,
    label="Backward simulations"
)

plt.scatter(
    SPILL_LON,
    SPILL_LAT,
    marker="*",
    s=250,
    label="Detected spill"
)

plt.scatter(
    lon_mean,
    lat_mean,
    marker="X",
    s=150,
    label="Mean source estimate"
)

# 95% bounding box
plt.plot(
    [
        lon_95_low,
        lon_95_high,
        lon_95_high,
        lon_95_low,
        lon_95_low
    ],
    [
        lat_95_low,
        lat_95_low,
        lat_95_high,
        lat_95_high,
        lat_95_low
    ],
    linestyle="--",
    linewidth=2,
    label="Approx. 95% source region"
)

plt.xlabel(
    "Longitude"
)

plt.ylabel(
    "Latitude"
)

plt.title(
    "Probabilistic Backward Oil-Drift Source Estimate"
)

plt.grid(True)

plt.legend()

plt.tight_layout()

plot_file = (
    "outputs/source_uncertainty.png"
)

plt.savefig(
    plot_file,
    dpi=200
)

plt.show()

print()
print(
    "Plot saved to:"
)

print(
    plot_file
)