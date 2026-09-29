import cv2
import os
import pandas as pd
import numpy as np
import torch
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

output_folder = "outputs"

os.makedirs(output_folder, exist_ok=True)


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

print("Total test images:", len(test_data))


# --------------------------------
# Load trained U-Net
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
# Generate predictions
# --------------------------------

# First 3 test images
for index in range(3):

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


    # Load image and ground truth
    image = Image.open(image_path).convert("RGB")

    ground_truth = Image.open(mask_path)


    # Prepare image
    image_tensor = transform(image)

    image_tensor = image_tensor.unsqueeze(0).to(device)


    # Prediction
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
    # Remove tiny isolated regions
    # --------------------------------

    prediction_uint8 = (
        prediction.astype(np.uint8) * 255
    )

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        prediction_uint8,
        connectivity=8
    )

    min_area = 20

    cleaned_prediction = np.zeros_like(prediction_uint8)

    for label in range(1, num_labels):

        area = stats[label, cv2.CC_STAT_AREA]

        if area >= min_area:
            cleaned_prediction[labels == label] = 255

    prediction = (
        cleaned_prediction > 0
    ).astype(np.float32)
        
    # Resize ground truth for display
    ground_truth_display = ground_truth.resize(
        (256, 256),
        Image.Resampling.NEAREST
    )

    ground_truth_array = np.array(
        ground_truth_display
    )

    ground_truth_array = (
        ground_truth_array > 0
    ).astype(np.float32)


    # --------------------------------
    # Calculate Dice
    # --------------------------------

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


    print(
        f"Test image {index + 1}: "
        f"Dice = {dice:.4f}"
    )


    # --------------------------------
    # Create visualization
    # --------------------------------

    plt.figure(figsize=(15, 5))


    plt.subplot(1, 3, 1)

    plt.imshow(image)

    plt.title("Original SAR Image")

    plt.axis("off")


    plt.subplot(1, 3, 2)

    plt.imshow(
        ground_truth_array,
        cmap="gray"
    )

    plt.title("Ground Truth")

    plt.axis("off")


    plt.subplot(1, 3, 3)

    plt.imshow(
        prediction,
        cmap="gray"
    )

    plt.title(
        f"U-Net Prediction\nDice: {dice:.4f}"
    )

    plt.axis("off")


    plt.tight_layout()


    # --------------------------------
    # Save result
    # --------------------------------

    output_path = os.path.join(
        output_folder,
        f"test_prediction_{index + 1}.png"
    )

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.show()

    plt.close()


print()
print("Finished.")
print("Results saved in:", output_folder)