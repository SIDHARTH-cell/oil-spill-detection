import os
import pandas as pd
import numpy as np
import torch

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
# Device
# --------------------------------

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("Using device:", device)


# --------------------------------
# Load test data
# --------------------------------

test_data = pd.read_csv(test_csv)

print("Number of test images:", len(test_data))


# --------------------------------
# Load model
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
# Image transformation
# --------------------------------

transform = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.ToTensor()
])


# --------------------------------
# Dice function
# --------------------------------

def calculate_dice(prediction, ground_truth):

    intersection = (
        prediction * ground_truth
    ).sum()

    dice = (
        2 * intersection + 1e-7
    ) / (
        prediction.sum()
        + ground_truth.sum()
        + 1e-7
    )

    return dice


# --------------------------------
# Evaluate all test images
# --------------------------------

dice_scores = []


for index in range(len(test_data)):

    image_relative_path = test_data.iloc[index]["image_path"]
    mask_relative_path = test_data.iloc[index]["mask_path"]

    image_path = os.path.join(
        dataset_root,
        image_relative_path.replace("/", os.sep)
    )

    mask_path = os.path.join(
        dataset_root,
        mask_relative_path.replace("/", os.sep)
    )


    # Load image
    image = Image.open(image_path).convert("RGB")

    # Load ground truth
    ground_truth = Image.open(mask_path)


    # Prepare image
    image_tensor = transform(image)

    image_tensor = image_tensor.unsqueeze(0)

    image_tensor = image_tensor.to(device)


    # Prediction
    with torch.no_grad():

        output = model(image_tensor)

        probability = torch.sigmoid(output)

        prediction = (
            probability > 0.5
        ).float()


    # Convert prediction to NumPy
    prediction = (
        prediction
        .squeeze()
        .cpu()
        .numpy()
    )


    # Prepare ground truth
    ground_truth = ground_truth.resize(
        (256, 256),
        Image.Resampling.NEAREST
    )

    ground_truth = np.array(
        ground_truth
    )

    ground_truth = (
        ground_truth > 0
    ).astype(np.float32)


    # Calculate Dice
    dice = calculate_dice(
        prediction,
        ground_truth
    )


    dice_scores.append(dice)


    print(
        f"Image {index + 1:02d}/{len(test_data)} "
        f"Dice: {dice:.4f}"
    )


# --------------------------------
# Final result
# --------------------------------

mean_dice = np.mean(dice_scores)

print()
print("--------------------------------")
print("FINAL TEST RESULT")
print("--------------------------------")

print(
    f"Mean Test Dice: {mean_dice:.4f}"
)

print(
    f"Minimum Dice: {np.min(dice_scores):.4f}"
)

print(
    f"Maximum Dice: {np.max(dice_scores):.4f}"
)