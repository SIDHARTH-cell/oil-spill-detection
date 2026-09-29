import pandas as pd
import zstandard as zstd
from pathlib import Path
import csv

INPUT_FILE = Path("ais/data/ais-2020-07-27.csv.zst")
OUTPUT_FILE = Path("outputs/ais_vessels.csv")

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

# Spill area
LAT_MIN = 19.0
LAT_MAX = 20.5

LON_MIN = -93.0
LON_MAX = -91.0

CHUNK_SIZE = 100_000

print("Opening AIS file...")

with open(INPUT_FILE, "rb") as compressed:
    dctx = zstd.ZstdDecompressor()

    with dctx.stream_reader(compressed) as reader:

        # Read CSV in chunks without loading everything into RAM
        for chunk_number, chunk in enumerate(
            pd.read_csv(
                reader,
                sep=",",
                chunksize=CHUNK_SIZE,
                low_memory=False
            )
        ):

            print(f"Processing chunk {chunk_number + 1}...", end="\r")

            # Make column names easier to handle
            chunk.columns = [
                str(c).strip().lower().replace("\ufeff", "")
                for c in chunk.columns
            ]

            # Show columns on first chunk
            if chunk_number == 0:
                print("\nColumns:")
                print(chunk.columns.tolist())

            # Adjust these names if NOAA file uses different capitalization
            lat_col = "latitude"
            lon_col = "longitude"

            if lat_col not in chunk.columns or lon_col not in chunk.columns:
                print("\nCould not find LAT/LON columns.")
                print(chunk.columns.tolist())
                break

            # Convert coordinates
            chunk[lat_col] = pd.to_numeric(
                chunk[lat_col],
                errors="coerce"
            )

            chunk[lon_col] = pd.to_numeric(
                chunk[lon_col],
                errors="coerce"
            )

            # Spatial filter
            filtered = chunk[
                (chunk[lat_col] >= LAT_MIN) &
                (chunk[lat_col] <= LAT_MAX) &
                (chunk[lon_col] >= LON_MIN) &
                (chunk[lon_col] <= LON_MAX)
            ]

            if len(filtered) == 0:
                continue

            # Append results
            write_header = not OUTPUT_FILE.exists()

            filtered.to_csv(
                OUTPUT_FILE,
                mode="a",
                index=False,
                header=write_header
            )

print()
print()
print("Filtering complete.")

if OUTPUT_FILE.exists():
    df = pd.read_csv(OUTPUT_FILE)

    print(f"Records found: {len(df)}")

    print("\nActual columns:")
    print(df.columns.tolist())

    # Find MMSI column regardless of capitalization/extra spaces
    mmsi_column = None

    for col in df.columns:
        clean = str(col).strip().lower()

        if clean == "mmsi":
            mmsi_column = col
            break

    if mmsi_column:
        print(f"Unique vessels: {df[mmsi_column].nunique()}")
    else:
        print("MMSI column was not found.")

    print()
    print("Saved to:")
    print(OUTPUT_FILE)

else:
    print("No AIS records found in this region.")