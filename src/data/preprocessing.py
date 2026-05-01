import albumentations as A
from albumentations.pytorch import ToTensorV2
import numpy as np
from src.utils.config import IMG_SIZE


def get_train_transforms(use_advanced_aug: bool = False) -> A.Compose:
    """
    Training augmentation pipeline.

    Args:
        use_advanced_aug: if True, adds GridDistortion + CoarseDropout
                          (used from Exp 06 onwards)
    """
    transforms = [
        A.Resize(IMG_SIZE, IMG_SIZE),
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.3),
        A.RandomRotate90(p=0.3),
        A.ShiftScaleRotate(shift_limit=0.1, scale_limit=0.1,
                           rotate_limit=30, p=0.5),
        A.ColorJitter(brightness=0.2, contrast=0.2,
                      saturation=0.2, hue=0.1, p=0.5),
        A.RandomResizedCrop(height=IMG_SIZE, width=IMG_SIZE,
                            scale=(0.8, 1.0), p=0.3),
    ]

    if use_advanced_aug:
        transforms += [
            A.GridDistortion(p=0.2),          # elastic-like distortion
            A.CoarseDropout(                   # simulates occluded lesions
                max_holes=8, max_height=32,
                max_width=32, p=0.3
            ),
        ]

    transforms += [
        A.Normalize(mean=(0.485, 0.456, 0.406),   # ImageNet stats
                    std=(0.229, 0.224, 0.225)),
        ToTensorV2(),
    ]
    return A.Compose(transforms)


def get_val_transforms() -> A.Compose:
    """Deterministic validation pipeline — resize + normalize only."""
    return A.Compose([
        A.Resize(IMG_SIZE, IMG_SIZE),
        A.Normalize(mean=(0.485, 0.456, 0.406),
                    std=(0.229, 0.224, 0.225)),
        ToTensorV2(),
    ])


def mixup_batch(images: 'torch.Tensor', labels: 'torch.Tensor',
                alpha: float = 0.4):
    """
    Apply MixUp augmentation to a batch.

    Returns mixed images and a tuple (labels_a, labels_b, lam)
    for use with mixup_criterion.
    """
    import torch
    lam = np.random.beta(alpha, alpha)
    batch_size = images.size(0)
    idx = torch.randperm(batch_size)
    mixed = lam * images + (1 - lam) * images[idx]
    return mixed, labels, labels[idx], lam


def mixup_criterion(criterion, pred, labels_a, labels_b, lam):
    """Compute MixUp loss."""
    return lam * criterion(pred, labels_a) + (1 - lam) * criterion(pred, labels_b)
