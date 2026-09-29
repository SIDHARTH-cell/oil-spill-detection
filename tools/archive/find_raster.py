import os
import pandas as pd

dataset_root = r"D:\NewWork (2)\AI\oilspill-detection-dataset"

test_csv = os.path.join(
    dataset_root,
    "splits",
    "test.csv"
)

raster_folder = os.path.join(
    dataset_root,
    "RASTER",
    "IMG-TIFF",
    "8-BIT"
)

test_data = pd.read_csv(test_csv)

print("Checking test images for matching GeoTIFFs...\n")

found = 0

for i in range(len(test_data)):

    image_path = test_data.iloc[i]["image_path"]

    # Extract filename without extension
    filename = os.path.basename(image_path)
    filename_without_ext = os.path.splitext(filename)[0]

    raster_path = os.path.join(
        raster_folder,
        filename_without_ext + ".tiff"
    )

    if os.path.exists(raster_path):

        print("FOUND:")
        print(raster_path)
        print()

        found += 1

print("Total matching GeoTIFFs found:", found)