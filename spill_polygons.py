import os
import json
import pandas as pd
import numpy as np
import torch
import rasterio
import cv2

from PIL import Image
from torchvision import transforms
from rasterio.features import shapes

from models.unet import UNet


# --------------------------------
# Paths
# --------------------------------

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

output_folder = "outputs"

os.makedirs(output_folder, exist_ok=True)


# --------------------------------
# Select first test image
# --------------------------------

test_data = pd.read_csv(test_csv)

image_relative_path = test_data.iloc[0]["image_path"]

image_filename = os.path.basename(image_relative_path)

image_name = os.path.splitext(image_filename)[0]

image_path = os.path.join(
    dataset_root,
    image_relative_path.replace("/", os.sep)
)

tiff_path = os.path.join(
    raster_folder,
    image_name + ".tiff"
)


print("Testing:", image_name)


# --------------------------------
# Device
# --------------------------------

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("Using device:", device)


# --------------------------------
# Load U-Net
# --------------------------------

model = UNet().to(device)

model.load_state_dict(
    torch.load(
        "best_unet.pth",
        map_location=device
    )
)

model.eval()


# --------------------------------
# Load image
# --------------------------------

image = Image.open(image_path).convert("RGB")

transform = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.ToTensor()
])

image_tensor = transform(image)

image_tensor = image_tensor.unsqueeze(0).to(device)


# --------------------------------
# Prediction
# --------------------------------

with torch.no_grad():

    output = model(image_tensor)

    probability = torch.sigmoid(output)

    prediction = (
        probability > 0.5
    ).float()


prediction = (
    prediction
    .squeeze()
    .cpu()
    .numpy()
)


# --------------------------------
# Open GeoTIFF
# --------------------------------

with rasterio.open(tiff_path) as src:

    width = src.width
    height = src.height

    geo_transform = src.transform

    crs = src.crs


print("GeoTIFF size:", width, "x", height)
print("CRS:", crs)


# --------------------------------
# Resize prediction to GeoTIFF
# --------------------------------

prediction_image = Image.fromarray(
    (prediction * 255).astype(np.uint8)
)

prediction_image = prediction_image.resize(
    (width, height),
    Image.Resampling.NEAREST
)

prediction_full = np.array(
    prediction_image
)

prediction_full = (
    prediction_full > 127
)


# --------------------------------
# Remove tiny regions
# --------------------------------

mask_uint8 = (
    prediction_full.astype(np.uint8) * 255
)

num_labels, labels, stats, centroids = (
    cv2.connectedComponentsWithStats(
        mask_uint8,
        connectivity=8
    )
)

min_area = 20

cleaned_mask = np.zeros_like(
    prediction_full,
    dtype=np.uint8
)

kept_regions = 0

for label in range(1, num_labels):

    area = stats[
        label,
        cv2.CC_STAT_AREA
    ]

    if area >= min_area:

        cleaned_mask[
            labels == label
        ] = 1

        kept_regions += 1


print("Detected regions after cleaning:", kept_regions)


# --------------------------------
# Convert mask to geographic polygons
# --------------------------------

features = []

for geometry, value in shapes(
    cleaned_mask,
    mask=(cleaned_mask == 1),
    transform=geo_transform
):

    if value != 1:
        continue

    features.append({
        "type": "Feature",
        "properties": {
            "class": "oil_spill"
        },
        "geometry": geometry
    })


# --------------------------------
# Save GeoJSON
# --------------------------------

geojson = {
    "type": "FeatureCollection",
    "features": features
}

geojson_path = os.path.join(
    output_folder,
    "oil_spill_regions.geojson"
)

with open(
    geojson_path,
    "w"
) as f:

    json.dump(
        geojson,
        f,
        indent=2
    )


print()
print("================================")
print("GEOGRAPHIC SPILL REGIONS")
print("================================")

print(
    "Number of polygons:",
    len(features)
)

print(
    "GeoJSON saved to:",
    geojson_path
)


# --------------------------------
# Print polygon coordinate ranges
# --------------------------------

for i, feature in enumerate(features):

    geometry = feature["geometry"]

    coordinates = geometry["coordinates"]

    # Handle Polygon
    if geometry["type"] == "Polygon":

        outer_ring = coordinates[0]

    else:

        # Handle MultiPolygon
        outer_ring = coordinates[0][0]


    longitudes = [
        point[0]
        for point in outer_ring
    ]

    latitudes = [
        point[1]
        for point in outer_ring
    ]


    print()
    print(
        f"Region {i + 1}:"
    )

    print(
        "Longitude range:",
        min(longitudes),
        "to",
        max(longitudes)
    )

    print(
        "Latitude range:",
        min(latitudes),
        "to",
        max(latitudes)
    )