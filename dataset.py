import os
import pandas as pd
from PIL import Image

import torch
from torch.utils.data import Dataset
from torchvision import transforms


class OilSpillDataset(Dataset):

    def __init__(self, csv_file, dataset_root):

        self.data = pd.read_csv(csv_file)
        self.dataset_root = dataset_root

        self.image_transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor()
        ])

        self.mask_transform = transforms.Compose([
            transforms.Resize(
                (256, 256),
                interpolation=transforms.InterpolationMode.NEAREST
            ),
            transforms.PILToTensor()
        ])

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):

        row = self.data.iloc[index]

        image_path = os.path.join(
            self.dataset_root,
            row["image_path"].replace("/", os.sep)
        )

        mask_path = os.path.join(
            self.dataset_root,
            row["mask_path"].replace("/", os.sep)
        )

        image = Image.open(image_path).convert("RGB")
        mask = Image.open(mask_path)

        image = self.image_transform(image)

        mask = self.mask_transform(mask)
        mask = mask.squeeze(0).long()
        mask = (mask > 0).long()

        return image, mask