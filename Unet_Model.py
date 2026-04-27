from torchvision import models
import os
from PIL import Image
import torch
import torch.nn as nn
from torchvision import transforms
import numpy as np

#model
class FeatureFuse(nn.Module):

    def __init__(self, in_channels, out_channels):
        super(FeatureFuse, self).__init__()
        self.conv1x1 = nn.Conv2d(in_channels, out_channels, kernel_size=1, padding=0, bias=False)
        self.conv3x3 = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False)
        self.conv3x3_dilated = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=2, bias=False, dilation=2)
        self.norm = nn.BatchNorm2d(out_channels)

    def forward(self, x):
        x1 = self.conv1x1(x)
        x2 = self.conv3x3(x)
        x3 = self.conv3x3_dilated(x)
        out = self.norm(x1 + x2 + x3)
        return out


class ResidualBlock(nn.Module):
    def __init__(self, in_channels, out_channels, dropout=0.0):
        super(ResidualBlock, self).__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.LeakyReLU(0.1, inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.LeakyReLU(0.1, inplace=True),
            nn.Dropout2d(dropout)
        )
        self.residual = nn.Conv2d(in_channels, out_channels, kernel_size=1, padding=0, bias=False)
        self.norm = nn.BatchNorm2d(out_channels)

    def forward(self, x):
        residual = self.residual(x)
        out = self.block(x)
        out += residual
        out = self.norm(out)
        return out

class AggreUNet(nn.Module):
    def __init__(self, n_class):
        super(AggreUNet, self).__init__()
        self.base_model = models.resnet18(pretrained=True)
        self.base_layers = list(self.base_model.children())

        self.layer0 = nn.Sequential(*self.base_layers[:3])  # size=(N, 64, H/2, W/2)
        self.layer1 = nn.Sequential(*self.base_layers[3:5], FeatureFuse(64, 64))  # size=(N, 64, H/4, W/4)
        self.layer2 = nn.Sequential(self.base_layers[5], FeatureFuse(128, 128))  # size=(N, 128, H/8, W/8)
        self.layer3 = nn.Sequential(self.base_layers[6], FeatureFuse(256, 256))  # size=(N, 256, H/16, W/16)
        self.layer4 = nn.Sequential(self.base_layers[7], FeatureFuse(512, 512))  # size=(N, 512, H/32, W/32)

        self.upsample = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)

        self.conv_up3 = ResidualBlock(256 + 512, 512, 0.1)
        self.conv_up2 = ResidualBlock(128 + 512, 256, 0.1)
        self.conv_up1 = ResidualBlock(64 + 256, 256, 0.1)
        self.conv_up0 = ResidualBlock(64 + 256, 128, 0.1)

        self.conv_original_size0 = ResidualBlock(3, 64, 0.1)
        self.conv_original_size1 = ResidualBlock(64, 64, 0.1)
        self.conv_original_size2 = ResidualBlock(64 + 128, 64, 0.1)

        self.conv_last = nn.Conv2d(64, n_class, 1)

    def forward(self, input):
        x_original = self.conv_original_size0(input)
        x_original = self.conv_original_size1(x_original)

        layer0 = self.layer0(input)
        layer1 = self.layer1(layer0)
        layer2 = self.layer2(layer1)
        layer3 = self.layer3(layer2)
        layer4 = self.layer4(layer3)

        layer4 = self.conv_up3(torch.cat([self.upsample(layer4), layer3], dim=1))
        layer3 = self.conv_up2(torch.cat([self.upsample(layer4), layer2], dim=1))
        layer2 = self.conv_up1(torch.cat([self.upsample(layer3), layer1], dim=1))
        layer1 = self.conv_up0(torch.cat([self.upsample(layer2), layer0], dim=1))
        x = self.upsample(layer1)
        x = torch.cat([x, x_original], dim=1)
        out = self.conv_last(self.conv_original_size2(x))
        return out


image_transform = transforms.Compose([
    transforms.Resize((512, 512)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5143, 0.2719, 0.1609], std=[0.3434, 0.1802, 0.0979])
])


#prediction function
def Unet_evaluate_single_image(model, image_path, device):
    image = Image.open(image_path).convert('RGB')
    image = image_transform(image).unsqueeze(0).to(device)

    # 模型推理
    model.eval()
    with torch.no_grad():
        output = model(image)
        pred_mask = torch.sigmoid(output)
        pred_mask = (pred_mask > 0.5).float()

    return pred_mask


#save prediction file
def Unet_save_pred_mask(pred_mask, original_filename):
    pred_mask = pred_mask.squeeze().cpu().numpy()
    pred_mask = (pred_mask * 255).astype(np.uint8)
    pred_mask_img = Image.fromarray(pred_mask)
    result_dir = os.path.join('static', 'results')
    os.makedirs(result_dir, exist_ok=True)
    result_filename = f"result_{original_filename.rsplit('.', 1)[0]}.png"
    result_path = os.path.join(result_dir, result_filename)
    pred_mask_img.save(result_path, format="PNG")
    return result_filename


# Save the predicted mask
def Unet_save_pred_mask1(pred_mask, original_filename, result_folder='static/results'):
    pred_mask = pred_mask.squeeze().cpu().numpy()
    pred_mask = (pred_mask * 255).astype(np.uint8)
    pred_mask_img = Image.fromarray(pred_mask)
    os.makedirs(result_folder, exist_ok=True)
    clean_filename = os.path.basename(original_filename).replace("training", "").strip()
    result_filename = f"result_{clean_filename.rsplit('.', 1)[0]}.png"
    result_path = os.path.join(result_folder, result_filename)
    pred_mask_img.save(result_path, format="PNG")
    return result_path

def compute_metrics(preds, labels):
    preds = (preds > 0.5).float()

    intersection = (preds * labels).sum(dim=(1, 2, 3))
    union = preds.sum(dim=(1, 2, 3)) + labels.sum(dim=(1, 2, 3))
    dice = (2. * intersection) / (union + 1e-6)
    iou = intersection / (union - intersection + 1e-6)
    accuracy = (preds == labels).float().mean(dim=(1, 2, 3))
    recall = intersection / (labels.sum(dim=(1, 2, 3)) + 1e-6)
    precision = intersection / (preds.sum(dim=(1, 2, 3)) + 1e-6)
    f1_score = 2 * (precision * recall) / (precision + recall + 1e-6)

    return dice.mean().item(), iou.mean().item(), accuracy.mean().item(), recall.mean().item(), f1_score.mean().item()
