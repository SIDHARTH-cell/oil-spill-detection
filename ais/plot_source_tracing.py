import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# FILES
# ============================================================

AIS_FILE = "ais/synthetic_ais.csv"
DRIFT_FILE = "outputs/backward_drift.csv"


# ============================================================
# SPILL
# ============================================================

SPILL_LAT = 19.68805
SPILL_LON = -92.07878


# ============================================================
# LOAD DATA
# ============================================================

ais = pd.read_csv(AIS_FILE)

drift = pd.read_csv(DRIFT_FILE)

drift["time"] = pd.to_datetime(
    drift["time"],
    utc=True
)


# ============================================================
# PLOT
# ============================================================

plt.figure(figsize=(12, 9))


# ------------------------------------------------------------
# Vessel trajectories
# ------------------------------------------------------------

for mmsi, vessel in ais.groupby("mmsi"):

    vessel = vessel.sort_values(
        "base_date_time"
    )

    name = vessel["vessel_name"].iloc[0]

    # Highlight planted source vessel
    if str(mmsi) == "900000001":

        plt.plot(
            vessel["longitude"],
            vessel["latitude"],
            linewidth=3,
            label=f"{name} (planted source)"
        )

    else:

        plt.plot(
            vessel["longitude"],
            vessel["latitude"],
            linewidth=1,
            alpha=0.6,
            label=name
        )


# ------------------------------------------------------------
# Backward drift path
# ------------------------------------------------------------

plt.plot(
    drift["longitude"],
    drift["latitude"],
    linestyle="--",
    linewidth=3,
    label="Backward oil drift"
)


# ------------------------------------------------------------
# Detected spill
# ------------------------------------------------------------

plt.scatter(
    SPILL_LON,
    SPILL_LAT,
    marker="*",
    s=300,
    label="Detected spill"
)


# ------------------------------------------------------------
# Estimated source
# ------------------------------------------------------------

source = drift.iloc[-1]

plt.scatter(
    source["longitude"],
    source["latitude"],
    marker="X",
    s=200,
    label="Estimated source"
)


# ------------------------------------------------------------
# Labels
# ------------------------------------------------------------

plt.xlabel("Longitude")

plt.ylabel("Latitude")

plt.title(
    "Synthetic Oil Spill Source-Tracing Demonstration"
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

output_file = (
    "outputs/source_tracing_map.png"
)

plt.savefig(
    output_file,
    dpi=200
)

print()
print("Source-tracing map saved to:")
print(output_file)

plt.show()