"""
test_data.py — Tests for data pipeline
========================================

Covers:
  - Config constants (paths, class names, label map)
  - Preprocessing transforms (output shape, dtype, value range)
  - HAM10000Dataset (skipped if dataset absent)
  - build_dataframes stratified split
"""

from __future__ import annotations

import numpy as np
import pytest
import torch

from src.utils.config import (
    CLASS_NAMES,
    IMG_SIZE,
    LABEL_MAP,
    NUM_CLASSES,
    REPO_ROOT,
)


# ── Config sanity checks ──────────────────────────────────────────────────────

class TestConfig:
    def test_class_names_count(self):
        """Must have exactly 7 classes."""
        assert len(CLASS_NAMES) == 7

    def test_class_names_sorted(self):
        """CLASS_NAMES must be alphabetically sorted (matches training label indices)."""
        assert CLASS_NAMES == sorted(CLASS_NAMES), (
            "CLASS_NAMES order matters — it defines the model output indices"
        )

    def test_class_names_values(self):
        """All 7 expected codes must be present."""
        expected = {"AKIEC", "BCC", "BKL", "DF", "MEL", "NV", "VASC"}
        assert set(CLASS_NAMES) == expected

    def test_num_classes_matches(self):
        assert NUM_CLASSES == len(CLASS_NAMES) == 7

    def test_label_map_covers_all_classes(self):
        """Every class code must have a human-readable name in LABEL_MAP."""
        for code in CLASS_NAMES:
            assert code in LABEL_MAP, f"{code} missing from LABEL_MAP"
            assert isinstance(LABEL_MAP[code], str)
            assert len(LABEL_MAP[code]) > 0

    def test_img_size_positive(self):
        assert IMG_SIZE > 0
        assert isinstance(IMG_SIZE, int)

    def test_repo_root_exists(self):
        assert REPO_ROOT.exists()


# ── Preprocessing transforms ─────────────────────────────────────────────────

class TestPreprocessing:
    """Test albumentations pipeline output shapes and value ranges."""

    def _make_random_rgb(self, h: int = 450, w: int = 600) -> np.ndarray:
        """Return a random uint8 H×W×3 image (simulates a raw dermatoscopy scan)."""
        rng = np.random.default_rng(42)
        return (rng.integers(0, 256, (h, w, 3), dtype=np.uint8))

    def test_val_transforms_output_shape(self):
        """Val pipeline must produce (3, IMG_SIZE, IMG_SIZE) tensor."""
        from src.data.preprocessing import get_val_transforms
        tfm = get_val_transforms()
        img = self._make_random_rgb()
        result = tfm(image=img)["image"]
        assert isinstance(result, torch.Tensor)
        assert result.shape == (3, IMG_SIZE, IMG_SIZE)

    def test_val_transforms_dtype(self):
        """Output tensor must be float32."""
        from src.data.preprocessing import get_val_transforms
        tfm = get_val_transforms()
        result = tfm(image=self._make_random_rgb())["image"]
        assert result.dtype == torch.float32

    def test_val_transforms_normalized_range(self):
        """After ImageNet normalisation values should roughly be in [-3, 3]."""
        from src.data.preprocessing import get_val_transforms
        tfm = get_val_transforms()
        result = tfm(image=self._make_random_rgb())["image"]
        assert result.min().item() > -4.0
        assert result.max().item() <  4.0

    def test_train_transforms_basic_output_shape(self):
        from src.data.preprocessing import get_train_transforms
        tfm = get_train_transforms(use_advanced_aug=False)
        result = tfm(image=self._make_random_rgb())["image"]
        assert result.shape == (3, IMG_SIZE, IMG_SIZE)

    def test_train_transforms_advanced_output_shape(self):
        """Advanced aug (GridDistortion + CoarseDropout) must not change shape."""
        from src.data.preprocessing import get_train_transforms
        tfm = get_train_transforms(use_advanced_aug=True)
        result = tfm(image=self._make_random_rgb())["image"]
        assert result.shape == (3, IMG_SIZE, IMG_SIZE)

    def test_val_transforms_deterministic(self):
        """Val transforms must be deterministic — same input → same output."""
        from src.data.preprocessing import get_val_transforms
        tfm = get_val_transforms()
        img = self._make_random_rgb()
        out1 = tfm(image=img.copy())["image"]
        out2 = tfm(image=img.copy())["image"]
        assert torch.allclose(out1, out2)


# ── Dataset & split ───────────────────────────────────────────────────────────

class TestBuildDataframes:
    """Stratified split tests — skipped if dataset CSV is absent."""

    @pytest.fixture(autouse=True)
    def _require_csv(self):
        from src.utils.config import GROUND_TRUTH_CSV
        if not GROUND_TRUTH_CSV.exists():
            pytest.skip("HAM10000 CSV not found — skipping dataset tests")

    def test_split_sizes(self):
        from src.data.dataset import build_dataframes
        train_df, val_df = build_dataframes()
        total = len(train_df) + len(val_df)
        assert total == 10015, f"Expected 10015 samples, got {total}"
        assert abs(len(val_df) / total - 0.2) < 0.01   # ~20 % val

    def test_split_no_overlap(self):
        """Train and val sets must have disjoint image IDs."""
        from src.data.dataset import build_dataframes
        train_df, val_df = build_dataframes()
        train_ids = set(train_df["image_id"])
        val_ids = set(val_df["image_id"])
        assert len(train_ids & val_ids) == 0

    def test_split_stratified(self):
        """Class distribution in val must roughly match full dataset."""
        from src.data.dataset import build_dataframes
        train_df, val_df = build_dataframes()
        full = len(train_df) + len(val_df)
        for cls in CLASS_NAMES:
            val_count = (val_df["label"] == cls).sum()
            full_count = (
                (train_df["label"] == cls).sum()
                + val_count
            )
            expected_val = full_count * 0.2
            # Allow ±3 samples tolerance
            assert abs(val_count - expected_val) <= 3, (
                f"Class {cls}: expected ~{expected_val:.0f} val samples, got {val_count}"
            )

    def test_dataset_getitem(self):
        """__getitem__ must return (tensor, int_label) with correct shapes."""
        from src.data.dataset import HAM10000Dataset, build_dataframes
        from src.data.preprocessing import get_val_transforms
        from src.utils.config import IMAGES_DIR
        _, val_df = build_dataframes()
        ds = HAM10000Dataset(val_df, images_dir=IMAGES_DIR, transform=get_val_transforms())
        img_tensor, label = ds[0]
        assert isinstance(img_tensor, torch.Tensor)
        assert img_tensor.shape == (3, IMG_SIZE, IMG_SIZE)
        assert isinstance(label, int)
        assert 0 <= label < NUM_CLASSES
