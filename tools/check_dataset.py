import torch
from dataset import OilSpillDataset

dataset_root = r"D:\NewWork (2)\AI\oilspill-detection-dataset"

train_csv = r"D:\NewWork (2)\AI\oilspill-detection-dataset\splits\train.csv"

dataset = OilSpillDataset(train_csv, dataset_root)

image, mask = dataset[0]

print("Number of training samples:", len(dataset))

print("Image shape:", image.shape)
print("Image data type:", image.dtype)

print("Mask shape:", mask.shape)
print("Mask data type:", mask.dtype)

print("Mask values:", torch.unique(mask))