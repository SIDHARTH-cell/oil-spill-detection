import csv
import math
from datetime import datetime, timedelta
from pathlib import Path


# ============================================================
# TIME
# ============================================================

START_TIME = datetime(
    2020, 7, 26, 16, 15, 46
)

END_TIME = datetime(
    2020, 7, 27, 0, 15, 46
)

INTERVAL_MINUTES = 10


# ============================================================
# OUTPUT
# ============================================================

OUTPUT_FILE = Path(
    "ais/synthetic_environment.csv"
)


# ============================================================
# SYNTHETIC ENVIRONMENT
# ============================================================

def environmental_conditions(hours_before_spill):

    """
    Generate changing synthetic environmental conditions.

    These values are for demonstration only.
    They are NOT historical measurements.
    """

    # Current gradually changes direction
    current_direction = (
        100.0
        + 8.0 * math.sin(
            hours_before_spill * 0.8
        )
    )

    # Current speed changes slightly
    current_speed = (
        0.75
        + 0.15 * math.sin(
            hours_before_spill * 1.1
        )
    )

    # Wind direction changes more strongly
    wind_direction = (
        90.0
        + 15.0 * math.sin(
            hours_before_spill * 0.6
        )
    )

    # Wind speed varies
    wind_speed = (
        7.0
        + 2.0 * math.cos(
            hours_before_spill * 0.7
        )
    )

    return (
        current_speed,
        current_direction,
        wind_speed,
        wind_direction
    )


# ============================================================
# GENERATE
# ============================================================

rows = []

current_time = START_TIME

while current_time <= END_TIME:

    seconds_before = (
        END_TIME - current_time
    ).total_seconds()

    hours_before = (
        seconds_before / 3600.0
    )

    (
        current_speed,
        current_direction,
        wind_speed,
        wind_direction
    ) = environmental_conditions(
        hours_before
    )

    rows.append({

        "timestamp":
            current_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

        "wind_speed_knots":
            round(wind_speed, 3),

        "wind_direction_deg":
            round(wind_direction, 3),

        "current_speed_knots":
            round(current_speed, 3),

        "current_direction_deg":
            round(current_direction, 3)
    })

    current_time += timedelta(
        minutes=INTERVAL_MINUTES
    )


# ============================================================
# SAVE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    exist_ok=True
)

with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    fieldnames = [
        "timestamp",
        "wind_speed_knots",
        "wind_direction_deg",
        "current_speed_knots",
        "current_direction_deg"
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(rows)


# ============================================================
# OUTPUT
# ============================================================

print()
print(
    "Time-varying synthetic environment created."
)

print()
print(
    "Records:",
    len(rows)
)

print()
print(
    "Saved to:"
)

print(
    OUTPUT_FILE
)

print()
print(
    "NOTE: These environmental values are synthetic."
)