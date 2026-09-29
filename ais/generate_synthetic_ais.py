import csv
import math
import random
from datetime import datetime, timedelta
from pathlib import Path


# ============================================================
# REAL SENTINEL-1 SPILL LOCATION
# ============================================================

SPILL_LAT = 19.68805
SPILL_LON = -92.07878

SPILL_TIME = datetime(2020, 7, 27, 0, 15, 46)

# AIS interval
INTERVAL_MINUTES = 10

# Generate 8 hours of AIS before and after detection
START_TIME = SPILL_TIME - timedelta(hours=8)
END_TIME = SPILL_TIME + timedelta(hours=2)


# ============================================================
# OUTPUT
# ============================================================

OUTPUT_DIR = Path("ais")
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "synthetic_ais.csv"
GROUND_TRUTH_FILE = OUTPUT_DIR / "synthetic_ground_truth.txt"


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def destination_point(lat, lon, speed_knots, course_deg, minutes):
    """
    Move a vessel from lat/lon using speed and course.

    This is a simple approximation suitable for our demo.
    """

    # Nautical miles travelled
    distance_nm = speed_knots * minutes / 60.0

    # Convert nautical miles to degrees
    distance_deg = distance_nm / 60.0

    course = math.radians(course_deg)

    dlat = distance_deg * math.cos(course)

    # Correct longitude for latitude
    dlon = (
        distance_deg * math.sin(course)
        / math.cos(math.radians(lat))
    )

    return lat + dlat, lon + dlon


def course_between(lat1, lon1, lat2, lon2):
    """
    Calculate approximate bearing from point 1 to point 2.
    """

    dlon = math.radians(lon2 - lon1)

    y = math.sin(dlon) * math.cos(math.radians(lat2))

    x = (
        math.cos(math.radians(lat1)) *
        math.sin(math.radians(lat2))
        -
        math.sin(math.radians(lat1)) *
        math.cos(math.radians(lat2)) *
        math.cos(dlon)
    )

    bearing = math.degrees(math.atan2(y, x))

    return (bearing + 360) % 360


def interpolate_position(
    start_lat,
    start_lon,
    end_lat,
    end_lon,
    fraction
):
    """
    Linear interpolation for synthetic tracks.
    """

    lat = start_lat + (end_lat - start_lat) * fraction
    lon = start_lon + (end_lon - start_lon) * fraction

    return lat, lon


# ============================================================
# VESSEL DEFINITIONS
# ============================================================

# Each vessel has a deliberately different behavior.
#
# Vessel 1:
#   The planted source vessel.
#   Its track passes through the spill location.
#
# Vessel 2:
#   Passes close to spill but trajectory is different.
#
# Vessel 3:
#   Moves away from spill.
#
# Vessel 4:
#   Far from spill.
#
# Vessel 5:
#   Slow vessel near the area.
#
# Vessel 6:
#   AIS gap.
#
# Vessel 7:
#   Another nearby vessel.
#
# Vessel 8:
#   Vessel that crosses the region later.

vessels = [

    {
        "mmsi": "900000001",
        "name": "OCEAN STAR",
        "type": "Cargo",
        "start": (19.30, -92.65),
        "target": (SPILL_LAT, SPILL_LON),
        "speed": 12.0,
        "behavior": "source_candidate",
    },

    {
        "mmsi": "900000002",
        "name": "BLUE HORIZON",
        "type": "Tanker",
        "start": (19.95, -92.35),
        "target": (19.75, -92.10),
        "speed": 11.0,
        "behavior": "nearby_crossing",
    },

    {
        "mmsi": "900000003",
        "name": "PACIFIC TRADER",
        "type": "Cargo",
        "start": (19.85, -91.80),
        "target": (20.20, -91.50),
        "speed": 13.0,
        "behavior": "moving_away",
    },

    {
        "mmsi": "900000004",
        "name": "MARINE SPIRIT",
        "type": "Cargo",
        "start": (18.90, -92.90),
        "target": (18.95, -92.70),
        "speed": 10.0,
        "behavior": "far_vessel",
    },

    {
        "mmsi": "900000005",
        "name": "COASTAL DREAM",
        "type": "Fishing",
        "start": (19.55, -92.20),
        "target": (19.60, -92.15),
        "speed": 4.0,
        "behavior": "slow_nearby",
    },

    {
        "mmsi": "900000006",
        "name": "NORTH WIND",
        "type": "Cargo",
        "start": (19.20, -92.00),
        "target": (19.80, -92.00),
        "speed": 9.0,
        "behavior": "ais_gap",
    },

    {
        "mmsi": "900000007",
        "name": "SEA FALCON",
        "type": "Tanker",
        "start": (19.90, -92.60),
        "target": (19.50, -92.20),
        "speed": 10.0,
        "behavior": "nearby_crossing",
    },

    {
        "mmsi": "900000008",
        "name": "WESTERN DAWN",
        "type": "Cargo",
        "start": (19.60, -93.00),
        "target": (19.60, -92.50),
        "speed": 14.0,
        "behavior": "crossing",
    },
]


# ============================================================
# GENERATE TRACKS
# ============================================================

random.seed(42)

rows = []

current_time = START_TIME

while current_time <= END_TIME:

    total_seconds = (
        END_TIME - START_TIME
    ).total_seconds()

    elapsed_seconds = (
        current_time - START_TIME
    ).total_seconds()

    fraction = elapsed_seconds / total_seconds

    for vessel in vessels:

        start_lat, start_lon = vessel["start"]
        target_lat, target_lon = vessel["target"]

        # ----------------------------------------------------
        # AIS GAP
        # ----------------------------------------------------

        if vessel["behavior"] == "ais_gap":

            # Hide AIS for 90 minutes around the spill
            gap_start = SPILL_TIME - timedelta(minutes=45)
            gap_end = SPILL_TIME + timedelta(minutes=45)

            if gap_start <= current_time <= gap_end:
                continue

        # ----------------------------------------------------
        # NORMAL INTERPOLATED POSITION
        # ----------------------------------------------------

                # ----------------------------------------------------
        # SOURCE VESSEL
        #
        # OCEAN STAR must reach the spill location exactly
        # at the Sentinel-1 detection time.
        # ----------------------------------------------------

        if vessel["behavior"] == "source_candidate":

            # Time required to travel from START to spill
            travel_seconds = (
                SPILL_TIME - START_TIME
            ).total_seconds()

            elapsed_seconds = (
                current_time - START_TIME
            ).total_seconds()

            if elapsed_seconds <= travel_seconds:

                fraction_to_spill = (
                    elapsed_seconds / travel_seconds
                )

                lat, lon = interpolate_position(
                    start_lat,
                    start_lon,
                    SPILL_LAT,
                    SPILL_LON,
                    fraction_to_spill
                )

            else:

                # After reaching the spill, continue moving
                # in the same direction.

                course = course_between(
                    start_lat,
                    start_lon,
                    SPILL_LAT,
                    SPILL_LON
                )

                minutes_after_spill = (
                    current_time - SPILL_TIME
                ).total_seconds() / 60

                lat, lon = destination_point(
                    SPILL_LAT,
                    SPILL_LON,
                    vessel["speed"],
                    course,
                    minutes_after_spill
                )

        else:

            # ------------------------------------------------
            # NORMAL VESSEL TRAJECTORY
            # ------------------------------------------------

            lat, lon = interpolate_position(
                start_lat,
                start_lon,
                target_lat,
                target_lon,
                fraction
            )

        # Add very small realistic GPS/AIS noise
        lat += random.uniform(-0.0005, 0.0005)
        lon += random.uniform(-0.0005, 0.0005)

        # Course
        course = course_between(
            start_lat,
            start_lon,
            target_lat,
            target_lon
        )

        # Small course variation
        course += random.uniform(-2, 2)
        course %= 360

        # Speed variation
        speed = vessel["speed"] + random.uniform(-0.5, 0.5)

        rows.append({
            "mmsi": vessel["mmsi"],
            "base_date_time": current_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "longitude": round(lon, 6),
            "latitude": round(lat, 6),
            "sog": round(max(speed, 0), 2),
            "cog": round(course, 2),
            "heading": round(course, 2),
            "vessel_name": vessel["name"],
            "vessel_type": vessel["type"],
        })

    current_time += timedelta(minutes=INTERVAL_MINUTES)


# ============================================================
# SAVE CSV
# ============================================================

fieldnames = [
    "mmsi",
    "base_date_time",
    "longitude",
    "latitude",
    "sog",
    "cog",
    "heading",
    "vessel_name",
    "vessel_type",
]


with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(rows)


# ============================================================
# SAVE GROUND TRUTH SEPARATELY
# ============================================================

with open(
    GROUND_TRUTH_FILE,
    "w",
    encoding="utf-8"
) as f:

    f.write("SYNTHETIC DATASET\n")
    f.write("=================\n\n")

    f.write(
        "This dataset is SYNTHETIC and is not real AIS data.\n\n"
    )

    f.write(
        f"Spill latitude: {SPILL_LAT}\n"
    )

    f.write(
        f"Spill longitude: {SPILL_LON}\n"
    )

    f.write(
        f"Spill time: {SPILL_TIME} UTC\n\n"
    )

    f.write(
        "Planted source vessel: 900000001\n"
    )

    f.write(
        "Vessel name: OCEAN STAR\n"
    )


# ============================================================
# SUMMARY
# ============================================================

print()
print("Synthetic AIS generation complete!")
print()

print("Records:", len(rows))
print(
    "Vessels:",
    len(vessels)
)

print()
print("Spill:")
print(f"  Latitude : {SPILL_LAT}")
print(f"  Longitude: {SPILL_LON}")
print(f"  Time     : {SPILL_TIME} UTC")

print()
print("Ground-truth source vessel:")
print("  MMSI: 900000001")
print("  Name: OCEAN STAR")

print()
print("Files created:")
print(f"  {OUTPUT_FILE}")
print(f"  {GROUND_TRUTH_FILE}")