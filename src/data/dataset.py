import os
import cv2
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset
from pathlib import Path
from typing import Optional, Callable

from src.utils.config import (
    IMAGES_DIR,
    GROUND_TRUTH_CSV,
    LABEL_COLS,
    CLASS_NAMES,
    NUM_CLASSES,
    VAL_SPLIT,
    SEED,
)


class HAM10000Dataset(Dataset):
    """
    PyTorch Dataset for ISIC 2018 Task 3 (HAM10000).

    Args:
        df          : DataFrame with columns ['image_id', 'label']
                      where 'label' is an integer class index.
        images_dir  : Directory containing <image_id>.jpg files.
        transform   : Albumentations Compose transform (or None).
    """

    def __init__(
        self,
        df: pd.DataFrame,
        images_dir: Path,
        transform: Optional[Callable] = None,
    ):
        self.df = df.reset_index(drop=True)
        self.images_dir = Path(images_dir)
        self.transform = transform

    # ------------------------------------------------------------------
    def __len__(self) -> int:
        return len(self.df)

    # ------------------------------------------------------------------
    def __getitem__(self, idx: int):
        row = self.df.iloc[idx]
        image_path = self.images_dir / f"{row['image_id']}.jpg"

        # Load as HWC uint8 (OpenCV reads BGR → convert to RGB)
        img = cv2.imread(str(image_path))
        if img is None:
            raise FileNotFoundError(f"Image not found: {image_path}")
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)   # (H, W, 3)

        if self.transform is not None:
            transformed = self.transform(image=img)
            img = transformed["image"]               # now a tensor (C, H, W)
        else:
            img = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0

        label = int(row["label"])
        return img, label


# ---------------------------------------------------------------------------
# Helper: build train/val DataFrames from the ISIC ground-truth CSV
# ---------------------------------------------------------------------------

def build_dataframes(
    csv_path: Path = GROUND_TRUTH_CSV,
    val_split: float = VAL_SPLIT,
    seed: int = SEED,
    stratify: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Read the one-hot ISIC CSV, decode labels, and split into train/val.

    Returns:
        train_df, val_df — each with columns ['image_id', 'label']
    """
    df = pd.read_csv(csv_path)

    # Decode one-hot → integer label
    # CLASS_NAMES is sorted; LABEL_COLS order matches CSV columns
    df["label_name"] = df[LABEL_COLS].idxmax(axis=1)   # e.g. 'MEL'
    df["label"] = df["label_name"].map(
        {cls: i for i, cls in enumerate(CLASS_NAMES)}
    )

    # Keep only what we need
    df = df[["image"] + LABEL_COLS + ["label_name", "label"]].copy()
    df.rename(columns={"image": "image_id"}, inplace=True)

    if stratify:
        from sklearn.model_selection import train_test_split
        train_df, val_df = train_test_split(
            df,
            test_size=val_split,
            random_state=seed,
            stratify=df["label"],
        )
    else:
        n_val = int(len(df) * val_split)
        rng = np.random.default_rng(seed)
        val_idx = rng.choice(len(df), size=n_val, replace=False)
        mask = np.zeros(len(df), dtype=bool)
        mask[val_idx] = True
        train_df = df[~mask].copy()
        val_df = df[mask].copy()

    return train_df.reset_index(drop=True), val_df.reset_index(drop=True)
