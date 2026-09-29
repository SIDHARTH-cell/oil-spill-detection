import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from dataset import OilSpillDataset
from models.unet import UNet


# -----------------------------
# Paths
# -----------------------------

dataset_root = r"D:\NewWork (2)\AI\oilspill-detection-dataset"

train_csv = r"D:\NewWork (2)\AI\oilspill-detection-dataset\splits\train.csv"
val_csv = r"D:\NewWork (2)\AI\oilspill-detection-dataset\splits\val.csv"


# -----------------------------
# Device
# -----------------------------

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("Using device:", device)


# -----------------------------
# Datasets
# -----------------------------

train_dataset = OilSpillDataset(
    train_csv,
    dataset_root
)

val_dataset = OilSpillDataset(
    val_csv,
    dataset_root
)


# -----------------------------
# DataLoaders
# -----------------------------

train_loader = DataLoader(
    train_dataset,
    batch_size=4,
    shuffle=True,
    num_workers=0
)

val_loader = DataLoader(
    val_dataset,
    batch_size=4,
    shuffle=False,
    num_workers=0
)


print("Training images:", len(train_dataset))
print("Validation images:", len(val_dataset))


# -----------------------------
# Model
# -----------------------------

model = UNet().to(device)
# Load the best model from the first 20 epochs
model.load_state_dict(
    torch.load(
        "best_unet.pth",
        map_location=device
    )
)

print("Loaded existing best model.")


# -----------------------------
# Loss
# -----------------------------

bce_loss = nn.BCEWithLogitsLoss()


def dice_loss(predictions, targets):

    predictions = torch.sigmoid(predictions)

    predictions = predictions.reshape(-1)
    targets = targets.reshape(-1)

    intersection = (predictions * targets).sum()

    dice = (2 * intersection + 1e-7) / (
        predictions.sum() + targets.sum() + 1e-7
    )

    return 1 - dice


# -----------------------------
# Optimizer
# -----------------------------

optimizer = torch.optim.Adam(
    model.parameters(),
    lr=0.001
)


# -----------------------------
# Dice score
# -----------------------------

def dice_score(predictions, targets):

    predictions = torch.sigmoid(predictions)

    predictions = (predictions > 0.5).float()

    intersection = (predictions * targets).sum()

    dice = (2 * intersection + 1e-7) / (
        predictions.sum() + targets.sum() + 1e-7
    )

    return dice.item()


# -----------------------------
# Training
# -----------------------------

epochs = 100
start_epoch = 20

best_val_dice = 0.6987683176994324


for epoch in range(start_epoch, epochs):

    model.train()

    total_train_loss = 0.0

    for images, masks in train_loader:

        images = images.to(device)

        masks = masks.to(device)
        masks = masks.unsqueeze(1).float()

        optimizer.zero_grad()

        outputs = model(images)

        loss_bce = bce_loss(outputs, masks)

        loss_dice = dice_loss(outputs, masks)

        loss = loss_bce + loss_dice

        loss.backward()

        optimizer.step()

        total_train_loss += loss.item()


    # -------------------------
    # Validation
    # -------------------------

    model.eval()

    total_val_dice = 0.0

    with torch.no_grad():

        for images, masks in val_loader:

            images = images.to(device)

            masks = masks.to(device)
            masks = masks.unsqueeze(1).float()

            outputs = model(images)

            score = dice_score(outputs, masks)

            total_val_dice += score


    average_train_loss = (
        total_train_loss / len(train_loader)
    )

    average_val_dice = (
        total_val_dice / len(val_loader)
    )


    print(
        f"Epoch [{epoch + 1}/{epochs}] "
        f"Train Loss: {average_train_loss:.4f} "
        f"Val Dice: {average_val_dice:.4f}"
    )


    # -------------------------
    # Save best model
    # -------------------------

    if average_val_dice > best_val_dice:

        best_val_dice = average_val_dice

        torch.save(
            model.state_dict(),
            "best_unet.pth"
        )

        print("Saved best model!")


print("Training complete.")
print("Best validation Dice:", best_val_dice)