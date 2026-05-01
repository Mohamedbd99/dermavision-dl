"""
test_models.py — Tests for model architecture
===============================================

Covers:
  - DermaVisionModel forward pass (output shape, no NaN/Inf)
  - All three factory helpers (build_baseline_cnn, b3, b4)
  - Freeze/unfreeze behaviour
  - Differential LR param groups
  - Checkpoint loading (skipped if .pt absent)
"""

from __future__ import annotations

import pytest
import torch

from src.utils.config import CLASS_NAMES, IMG_SIZE, NUM_CLASSES


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_batch(bs: int = 2) -> torch.Tensor:
    """Random float32 batch of shape (bs, 3, IMG_SIZE, IMG_SIZE)."""
    return torch.randn(bs, 3, IMG_SIZE, IMG_SIZE)


# ── DermaVisionModel ─────────────────────────────────────────────────────────

class TestDermaVisionModel:
    """Unit tests for the generic DermaVisionModel wrapper."""

    def test_output_shape_b3(self):
        """EfficientNet-B3 forward pass must return (B, 7) logits."""
        from src.models.architecture import DermaVisionModel
        model = DermaVisionModel("efficientnet_b3", pretrained=False)
        model.eval()
        with torch.no_grad():
            out = model(_make_batch(2))
        assert out.shape == (2, NUM_CLASSES)

    def test_output_no_nan(self):
        """No NaN or Inf in logits."""
        from src.models.architecture import DermaVisionModel
        model = DermaVisionModel("efficientnet_b3", pretrained=False)
        model.eval()
        with torch.no_grad():
            out = model(_make_batch(4))
        assert torch.isfinite(out).all(), "Logits contain NaN or Inf"

    def test_output_shape_resnet50(self):
        from src.models.architecture import DermaVisionModel
        model = DermaVisionModel("resnet50", pretrained=False)
        model.eval()
        with torch.no_grad():
            out = model(_make_batch(2))
        assert out.shape == (2, NUM_CLASSES)

    def test_freeze_base(self):
        """When freeze_base=True, backbone parameters must not require grad."""
        from src.models.architecture import DermaVisionModel
        model = DermaVisionModel("efficientnet_b3", pretrained=False, freeze_base=True)
        for p in model.base.parameters():
            assert not p.requires_grad

    def test_unfreeze_base(self):
        """After unfreeze_base(), all backbone params should require grad."""
        from src.models.architecture import DermaVisionModel
        model = DermaVisionModel("efficientnet_b3", pretrained=False, freeze_base=True)
        model.unfreeze_base()
        for p in model.base.parameters():
            assert p.requires_grad

    def test_head_params_always_trainable(self):
        """Head params must always require grad, even when base is frozen."""
        from src.models.architecture import DermaVisionModel
        model = DermaVisionModel("efficientnet_b3", pretrained=False, freeze_base=True)
        for p in model.head.parameters():
            assert p.requires_grad

    def test_dropout_rate_applied(self):
        """Dropout layer must be present in head with the correct rate."""
        from src.models.architecture import DermaVisionModel
        model = DermaVisionModel("efficientnet_b3", pretrained=False, dropout=0.5)
        dropout_layers = [m for m in model.head if isinstance(m, torch.nn.Dropout)]
        assert len(dropout_layers) == 1
        assert abs(dropout_layers[0].p - 0.5) < 1e-6

    def test_num_output_classes(self):
        """Linear head output features must equal NUM_CLASSES."""
        from src.models.architecture import DermaVisionModel
        model = DermaVisionModel("efficientnet_b3", pretrained=False)
        linear_layers = [m for m in model.head if isinstance(m, torch.nn.Linear)]
        assert linear_layers[-1].out_features == NUM_CLASSES


# ── Factory helpers ───────────────────────────────────────────────────────────

class TestFactoryHelpers:
    def test_build_baseline_cnn(self):
        from src.models.architecture import build_baseline_cnn
        model = build_baseline_cnn()
        model.eval()
        with torch.no_grad():
            out = model(_make_batch())
        assert out.shape == (2, NUM_CLASSES)
        assert model.backbone_name == "resnet50"

    def test_build_efficientnet_b3(self):
        from src.models.architecture import build_efficientnet_b3
        model = build_efficientnet_b3(pretrained=False)
        model.eval()
        with torch.no_grad():
            out = model(_make_batch())
        assert out.shape == (2, NUM_CLASSES)

    def test_build_efficientnet_b4(self):
        from src.models.architecture import build_efficientnet_b4
        model = build_efficientnet_b4(pretrained=False)
        model.eval()
        with torch.no_grad():
            out = model(_make_batch())
        assert out.shape == (2, NUM_CLASSES)


# ── Param groups (differential LR) ───────────────────────────────────────────

class TestParamGroups:
    def test_two_param_groups(self):
        """get_param_groups must return exactly 2 groups: backbone + head."""
        from src.models.architecture import DermaVisionModel
        model = DermaVisionModel("efficientnet_b3", pretrained=False)
        groups = model.get_param_groups(base_lr=1e-4, head_lr_multiplier=10)
        assert len(groups) == 2

    def test_head_lr_multiplier(self):
        """Head group lr must equal base_lr × multiplier."""
        from src.models.architecture import DermaVisionModel
        model = DermaVisionModel("efficientnet_b3", pretrained=False)
        groups = model.get_param_groups(base_lr=1e-4, head_lr_multiplier=10)
        backbone_lr = groups[0]["lr"]
        head_lr = groups[1]["lr"]
        assert abs(backbone_lr - 1e-4) < 1e-10
        assert abs(head_lr - 1e-3) < 1e-10

    def test_param_groups_cover_all_params(self):
        """Union of both groups must include every parameter in the model."""
        from src.models.architecture import DermaVisionModel
        model = DermaVisionModel("efficientnet_b3", pretrained=False)
        groups = model.get_param_groups(base_lr=1e-4)
        all_group_params = set(
            id(p) for g in groups for p in g["params"]
        )
        all_model_params = set(id(p) for p in model.parameters())
        assert all_model_params == all_group_params


# ── Checkpoint loading ────────────────────────────────────────────────────────

class TestCheckpointLoading:
    """Verify the production checkpoint loads cleanly."""

    @pytest.fixture(autouse=True)
    def _require_checkpoint(self):
        from src.utils.config import CKPT_DIR
        ckpt = CKPT_DIR / "exp07-optuna-FINAL_best.pt"
        if not ckpt.exists():
            pytest.skip(f"Checkpoint not found: {ckpt}")
        self.ckpt_path = ckpt

    def test_checkpoint_loads_without_error(self):
        """State dict must load into DermaVisionModel without missing/extra keys."""
        from src.models.architecture import DermaVisionModel
        model = DermaVisionModel(
            backbone="efficientnet_b3",
            pretrained=False,
            dropout=0.229,
        )
        state_dict = torch.load(self.ckpt_path, map_location="cpu")
        missing, unexpected = model.load_state_dict(state_dict, strict=True)
        # strict=True already raises on mismatch, but let's be explicit
        assert missing == [], f"Missing keys: {missing}"
        assert unexpected == [], f"Unexpected keys: {unexpected}"

    def test_checkpoint_forward_pass(self):
        """Loaded model must produce valid (2, 7) output."""
        from src.models.architecture import DermaVisionModel
        model = DermaVisionModel(
            backbone="efficientnet_b3",
            pretrained=False,
            dropout=0.229,
        )
        state_dict = torch.load(self.ckpt_path, map_location="cpu")
        model.load_state_dict(state_dict)
        model.eval()
        with torch.no_grad():
            out = model(_make_batch(2))
        assert out.shape == (2, NUM_CLASSES)
        assert torch.isfinite(out).all()
