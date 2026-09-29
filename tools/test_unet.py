import torch
from models.unet import UNet

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = UNet().to(device)

x = torch.randn(1, 3, 256, 256).to(device)

output = model(x)

print("Device:", device)
print("Input shape:", x.shape)
print("Output shape:", output.shape)