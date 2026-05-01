"""
DermaVision model architectures.

Supported backbones (via timm):
  - efficientnet_b3   (Exp 02 onwards — default)
  - resnet50          (Exp 01 baseline)
  - efficientnet_b4   (Exp 07 scale-up)
"""

import torch
import torch.nn as nn
import timm

from src.utils.config import NUM_CLASSES


class DermaVisionModel(nn.Module):
    """
    Flexible wrapper around any timm backbone.

    Args:
        backbone    : timm model name (e.g. 'efficientnet_b3')
        num_classes : number of output classes (default: 7)
        pretrained  : use ImageNet pretrained weights
        dropout     : dropout rate before the final linear layer
        freeze_base : if True, freeze all backbone params (feature extraction mode)
    """

    def __init__(
        self,
        backbone: str = 'efficientnet_b3',
        num_classes: int = NUM_CLASSES,
        pretrained: bool = True,
        dropout: float = 0.3,
        freeze_base: bool = False,
    ):
        super().__init__()
        self.backbone_name = backbone

        # Load timm model with no head
        self.base = timm.create_model(
            backbone,
            pretrained=pretrained,
            num_classes=0,       # remove classifier
            global_pool='avg',   # global average pooling
        )
        in_features = self.base.num_features

        if freeze_base:
            for p in self.base.parameters():
                p.requires_grad = False

        # Custom head
        self.head = nn.Sequential(
            nn.Dropout(p=dropout),
            nn.Linear(in_features, num_classes),
        )

    # ------------------------------------------------------------------
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.base(x)        # (B, in_features)
        logits   = self.head(features) # (B, num_classes)
        return logits

    # ------------------------------------------------------------------
    def unfreeze_base(self):
        """Unfreeze backbone parameters (call for fine-tuning phase)."""
        for p in self.base.parameters():
            p.requires_grad = True

    def get_param_groups(self, base_lr: float, head_lr_multiplier: float = 10.0):
        """
        Return parameter groups for differential learning rates.
        Head gets base_lr * head_lr_multiplier.
        """
        return [
            {'params': self.base.parameters(), 'lr': base_lr},
            {'params': self.head.parameters(), 'lr': base_lr * head_lr_multiplier},
        ]


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

def build_baseline_cnn(num_classes: int = NUM_CLASSES) -> nn.Module:
    """
    Exp 01 — simple ResNet-50 baseline (no fancy tricks, no class weighting).
    Used as the dumb lower-bound reference.
    """
    return DermaVisionModel(
        backbone='resnet50',
        num_classes=num_classes,
        pretrained=True,
        dropout=0.2,
    )


def build_efficientnet_b3(
    num_classes: int = NUM_CLASSES,
    pretrained: bool = True,
    dropout: float = 0.3,
) -> DermaVisionModel:
    """Exp 02+ — default EfficientNet-B3 model."""
    return DermaVisionModel(
        backbone='efficientnet_b3',
        num_classes=num_classes,
        pretrained=pretrained,
        dropout=dropout,
    )


def build_efficientnet_b4(
    num_classes: int = NUM_CLASSES,
    pretrained: bool = True,
    dropout: float = 0.4,
) -> DermaVisionModel:
    """Exp 07 — scale-up to EfficientNet-B4."""
    return DermaVisionModel(
        backbone='efficientnet_b4',
        num_classes=num_classes,
        pretrained=pretrained,
        dropout=dropout,
    )
