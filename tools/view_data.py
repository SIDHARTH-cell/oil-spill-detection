from PIL import Image
import matplotlib.pyplot as plt

image_path = r"D:\NewWork (2)\AI\oilspill-detection-dataset\IMAGES\IMG-RGB\IMG_01_TILE_001.png"
mask_path = r"D:\NewWork (2)\AI\oilspill-detection-dataset\IMAGES\LABELS-1D\IMG_01_TILE_001_1D.png"

image = Image.open(image_path)
mask = Image.open(mask_path)

import numpy as np
mask_array = np.array(mask)
print("Unique mask values:", np.unique(mask_array))

print("Image size:", image.size)
print("Mask size:", mask.size)

plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.imshow(image)
plt.title("SAR Image")
plt.axis("off")

plt.subplot(1, 2, 2)
plt.imshow(mask, cmap="gray")
plt.title("Ground Truth Mask")
plt.axis("off")

plt.show()