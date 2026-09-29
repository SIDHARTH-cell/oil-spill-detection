import os
import pandas as pd
import torch
import numpy as np
import matplotlib.pyplot as plt

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


# --------------------------------
# Read test split
# --------------------------------

test_data = pd.read_csv(test_csv)

print("Number of test images:", len(test_data))


# Get first test image and mask

image_relative_path = test_data.iloc[0]["image_path"]
mask_relative_path = test_data.iloc[0]["mask_path"]


image_path = os.path.join(
    dataset_root,
    image_relative_path.replace("/", os.sep)
)

mask_path = os.path.join(
    dataset_root,
    mask_relative_path.replace("/", os.sep)
)


print("Testing image:", image_path)
print("Testing mask:", mask_path)


# --------------------------------
# Device
# --------------------------------

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("Using device:", device)


# --------------------------------
# Load trained model
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
# Load image and ground truth
# --------------------------------

image = Image.open(image_path).convert("RGB")

ground_truth = Image.open(mask_path)


# --------------------------------
# Prepare image
# --------------------------------

transform = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.ToTensor()
])

image_tensor = transform(image)

image_tensor = image_tensor.unsqueeze(0)

image_tensor = image_tensor.to(device)


# --------------------------------
# Make prediction
# --------------------------------

with torch.no_grad():

    output = model(image_tensor)

    probability = torch.sigmoid(output)

    prediction = (probability > 0.5).float()


# --------------------------------
# Convert prediction to NumPy
# --------------------------------

prediction = prediction.squeeze().cpu().numpy()

# --------------------------------
# Calculate Dice score
# --------------------------------

ground_truth_array = np.array(ground_truth)

# Resize ground truth to match prediction
ground_truth_array = np.array(
    Image.fromarray(ground_truth_array).resize(
        (256, 256),
        Image.Resampling.NEAREST
    )
)

# Convert mask to binary
ground_truth_array = (ground_truth_array > 0).astype(np.float32)

intersection = (
    prediction * ground_truth_array
).sum()

dice = (
    2 * intersection + 1e-7
) / (
    prediction.sum()
    + ground_truth_array.sum()
    + 1e-7
)

print("Test Dice Score:", dice)


# --------------------------------
# Display results
# --------------------------------

plt.figure(figsize=(15, 5))


plt.subplot(1, 3, 1)

plt.imshow(image)

plt.title("Original SAR Image")

plt.axis("off")


plt.subplot(1, 3, 2)

plt.imshow(ground_truth, cmap="gray")

plt.title("Ground Truth Mask")

plt.axis("off")


plt.subplot(1, 3, 3)

plt.imshow(prediction, cmap="gray")

plt.title("U-Net Prediction")

plt.axis("off")


plt.tight_layout()

plt.show()