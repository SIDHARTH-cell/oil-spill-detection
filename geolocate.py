import os
import pandas as pd
import numpy as np
import torch
import rasterio

from PIL import Image
from torchvision import transforms

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


# --------------------------------
# Read test data
# --------------------------------

test_data = pd.read_csv(test_csv)

# Use the first official test image
image_relative_path = test_data.iloc[0]["image_path"]

image_filename = os.path.basename(
    image_relative_path
)

image_name = os.path.splitext(
    image_filename
)[0]


print("Testing:", image_name)


# --------------------------------
# Find corresponding files
# --------------------------------

image_path = os.path.join(
    dataset_root,
    image_relative_path.replace("/", os.sep)
)

tiff_path = os.path.join(
    raster_folder,
    image_name + ".tiff"
)


print("Image:", image_path)
print("GeoTIFF:", tiff_path)


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

image_tensor = image_tensor.unsqueeze(0)

image_tensor = image_tensor.to(device)


# --------------------------------
# U-Net prediction
# --------------------------------

with torch.no_grad():

    output = model(image_tensor)

    probability = torch.sigmoid(output)

    prediction = (
        probability > 0.5
    ).float()


# Convert to NumPy
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

    transform_geo = src.transform

    crs = src.crs

    print()
    print("GeoTIFF width:", width)
    print("GeoTIFF height:", height)
    print("CRS:", crs)


# --------------------------------
# Resize prediction to GeoTIFF size
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
# Find oil pixels
# --------------------------------

rows, cols = np.where(
    prediction_full
)


print()
print("Number of predicted oil pixels:", len(rows))


# --------------------------------
# Convert pixels to coordinates
# --------------------------------

if len(rows) > 0:

    coordinates = []

    for row, col in zip(rows, cols):

        longitude, latitude = rasterio.transform.xy(
            transform_geo,
            row,
            col
        )

        coordinates.append(
            (latitude, longitude)
        )


    coordinates = np.array(
        coordinates
    )


    # --------------------------------
    # Calculate approximate centroid
    # --------------------------------

    centroid_latitude = coordinates[:, 0].mean()
    centroid_longitude = coordinates[:, 1].mean()


    print()
    print("================================")
    print("OIL SPILL LOCATION")
    print("================================")

    print(
        "Approximate latitude:",
        centroid_latitude
    )

    print(
        "Approximate longitude:",
        centroid_longitude
    )

else:

    print("No oil pixels detected.")