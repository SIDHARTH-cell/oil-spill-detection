import pandas as pd
import matplotlib.pyplot as plt

# --------------------------------------------------
# Files
# --------------------------------------------------

AIS_FILE = "ais/synthetic_ais.csv"

# Real detected spill location
SPILL_LAT = 19.68805
SPILL_LON = -92.07878


# --------------------------------------------------
# Load AIS
# --------------------------------------------------

df = pd.read_csv(AIS_FILE)

df["base_date_time"] = pd.to_datetime(
    df["base_date_time"]
)

print("AIS records:", len(df))
print("Vessels:", df["mmsi"].nunique())

print("\nVessels:")
print(
    df[["mmsi", "vessel_name", "vessel_type"]]
    .drop_duplicates()
    .to_string(index=False)
)


# --------------------------------------------------
# Plot
# --------------------------------------------------

plt.figure(figsize=(12, 8))

for mmsi, vessel in df.groupby("mmsi"):

    vessel = vessel.sort_values("base_date_time")

    plt.plot(
        vessel["longitude"],
        vessel["latitude"],
        marker=".",
        markersize=2,
        linewidth=1,
        label=vessel["vessel_name"].iloc[0]
    )


# --------------------------------------------------
# Spill
# --------------------------------------------------

plt.scatter(
    SPILL_LON,
    SPILL_LAT,
    marker="*",
    s=250,
    label="Detected Oil Spill"
)


# --------------------------------------------------
# Labels
# --------------------------------------------------

plt.xlabel("Longitude")
plt.ylabel("Latitude")

plt.title(
    "Synthetic AIS Vessel Trajectories and Detected Oil Spill"
)

plt.legend(
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.grid(True)

plt.tight_layout()

plt.savefig(
    "outputs/synthetic_ais_tracks.png",
    dpi=200
)

plt.show()