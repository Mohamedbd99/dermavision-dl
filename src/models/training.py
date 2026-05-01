"""
Training loop with MLflow logging.

Usage (from repo root):
    python -m src.models.training --exp_name "exp01-baseline" --backbone resnet50 --epochs 10
"""

import argparse
import time
from pathlib import Path
from typing import Optional

import mlflow
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from src.utils.config import (
    REPO_ROOT, IMAGES_DIR, CLASS_NAMES,
    BATCH_SIZE, NUM_EPOCHS, LR, WEIGHT_DECAY, SEED, NUM_WORKERS,
)
from src.utils.metrics import compute_metrics
from src.data.dataset import build_dataframes, HAM10000Dataset
from src.data.preprocessing import (
    get_train_transforms, get_val_transforms,
    mixup_batch, mixup_criterion,
)
from src.models.architecture import DermaVisionModel


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _seed_everything(seed: int):
    import random
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _get_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device('cuda')
    if torch.backends.mps.is_available():
        return torch.device('mps')
    return torch.device('cpu')


def _compute_class_weights(train_df, num_classes: int) -> torch.Tensor:
    """Inverse-frequency class weights, normalised to sum = num_classes."""
    counts = train_df['label'].value_counts().sort_index().values.astype(float)
    weights = 1.0 / counts
    weights = weights / weights.sum() * num_classes
    return torch.tensor(weights, dtype=torch.float32)


# ---------------------------------------------------------------------------
# Core train / eval steps
# ---------------------------------------------------------------------------

def _train_epoch(
    model: nn.Module,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
    use_mixup: bool = False,
    mixup_alpha: float = 0.4,
) -> dict:
    model.train()
    running_loss = 0.0
    all_preds, all_labels = [], []

    for imgs, labels in loader:
        imgs   = imgs.to(device)
        labels = labels.to(device)

        if use_mixup:
            imgs, labels_a, labels_b, lam = mixup_batch(imgs, labels, mixup_alpha)
            logits = model(imgs)
            loss = mixup_criterion(criterion, logits, labels_a, labels_b, lam)
            # For accuracy tracking use original labels_a
            preds = logits.argmax(dim=1)
            all_labels.extend(labels_a.cpu().numpy())
        else:
            logits = model(imgs)
            loss   = criterion(logits, labels)
            preds  = logits.argmax(dim=1)
            all_labels.extend(labels.cpu().numpy())

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * imgs.size(0)
        all_preds.extend(preds.cpu().numpy())

    n = len(loader.dataset)
    epoch_loss = running_loss / n
    accuracy   = (np.array(all_preds) == np.array(all_labels)).mean()
    return {'train_loss': epoch_loss, 'train_acc': accuracy}


@torch.no_grad()
def _val_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> dict:
    model.eval()
    running_loss = 0.0
    all_preds, all_labels, all_probs = [], [], []

    for imgs, labels in loader:
        imgs   = imgs.to(device)
        labels = labels.to(device)
        logits = model(imgs)
        loss   = criterion(logits, labels)

        probs = torch.softmax(logits, dim=1)
        preds = logits.argmax(dim=1)

        running_loss += loss.item() * imgs.size(0)
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())
        all_probs.extend(probs.cpu().numpy())

    n = len(loader.dataset)
    val_loss = running_loss / n
    metrics  = compute_metrics(
        np.array(all_labels),
        np.array(all_preds),
        np.array(all_probs),
    )
    metrics['val_loss'] = round(val_loss, 4)
    return metrics


# ---------------------------------------------------------------------------
# Main training function
# ---------------------------------------------------------------------------

def train(
    exp_name: str,
    backbone: str = 'efficientnet_b3',
    epochs: int = NUM_EPOCHS,
    batch_size: int = BATCH_SIZE,
    lr: float = LR,
    weight_decay: float = WEIGHT_DECAY,
    use_class_weights: bool = True,
    use_mixup: bool = False,
    mixup_alpha: float = 0.4,
    use_advanced_aug: bool = False,
    dropout: float = 0.3,
    scheduler: str = 'cosine',   # 'cosine' | 'step' | 'none'
    seed: int = SEED,
    resume_ckpt: Optional[str] = None,
    mlflow_uri: str = str(REPO_ROOT / 'mlruns'),
):
    _seed_everything(seed)
    device = _get_device()
    print(f"[train] device={device}, backbone={backbone}, exp={exp_name}")

    # ── Data ────────────────────────────────────────────────────────────
    train_df, val_df = build_dataframes(seed=seed)
    train_tf = get_train_transforms(use_advanced_aug=use_advanced_aug)
    val_tf   = get_val_transforms()

    train_ds = HAM10000Dataset(train_df, IMAGES_DIR, transform=train_tf)
    val_ds   = HAM10000Dataset(val_df,   IMAGES_DIR, transform=val_tf)

    train_loader = DataLoader(
        train_ds, batch_size=batch_size, shuffle=True,
        num_workers=NUM_WORKERS, pin_memory=True, drop_last=True,
    )
    val_loader = DataLoader(
        val_ds, batch_size=batch_size, shuffle=False,
        num_workers=NUM_WORKERS, pin_memory=True,
    )

    # ── Model ────────────────────────────────────────────────────────────
    model = DermaVisionModel(backbone=backbone, dropout=dropout).to(device)
    if resume_ckpt:
        model.load_state_dict(torch.load(resume_ckpt, map_location=device))
        print(f"[train] resumed from {resume_ckpt}")

    # ── Loss ─────────────────────────────────────────────────────────────
    if use_class_weights:
        cw = _compute_class_weights(train_df, len(CLASS_NAMES)).to(device)
        criterion = nn.CrossEntropyLoss(weight=cw)
        print(f"[train] class weights: {cw.cpu().numpy().round(3)}")
    else:
        criterion = nn.CrossEntropyLoss()

    # ── Optimizer ────────────────────────────────────────────────────────
    param_groups = model.get_param_groups(base_lr=lr, head_lr_multiplier=10.0)
    optimizer    = torch.optim.AdamW(param_groups, weight_decay=weight_decay)

    # ── Scheduler ────────────────────────────────────────────────────────
    if scheduler == 'cosine':
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=epochs, eta_min=1e-6
        )
    elif scheduler == 'step':
        sched = torch.optim.lr_scheduler.StepLR(
            optimizer, step_size=10, gamma=0.1
        )
    else:
        sched = None

    # ── MLflow ───────────────────────────────────────────────────────────
    mlflow.set_tracking_uri(mlflow_uri)
    mlflow.set_experiment(exp_name)

    best_auc  = 0.0
    ckpt_path = REPO_ROOT / 'checkpoints' / f"{exp_name}_best.pt"

    with mlflow.start_run(run_name=exp_name):
        mlflow.log_params({
            'backbone': backbone, 'epochs': epochs,
            'batch_size': batch_size, 'lr': lr,
            'weight_decay': weight_decay, 'dropout': dropout,
            'use_class_weights': use_class_weights,
            'use_mixup': use_mixup, 'mixup_alpha': mixup_alpha if use_mixup else 'N/A',
            'use_advanced_aug': use_advanced_aug,
            'scheduler': scheduler, 'seed': seed,
        })

        for epoch in range(1, epochs + 1):
            t0 = time.time()

            train_metrics = _train_epoch(
                model, train_loader, optimizer, criterion, device,
                use_mixup=use_mixup, mixup_alpha=mixup_alpha,
            )
            val_metrics = _val_epoch(model, val_loader, criterion, device)

            if sched is not None:
                sched.step()

            elapsed = time.time() - t0
            all_metrics = {**train_metrics, **val_metrics, 'epoch_time_s': round(elapsed, 1)}

            mlflow.log_metrics(all_metrics, step=epoch)

            print(
                f"Epoch {epoch:03d}/{epochs} | "
                f"loss {train_metrics['train_loss']:.4f} → {val_metrics['val_loss']:.4f} | "
                f"acc {train_metrics['train_acc']:.3f} → {val_metrics['accuracy']:.3f} | "
                f"AUC {val_metrics['auc_roc']:.3f} | "
                f"{elapsed:.0f}s"
            )

            # Save best checkpoint (by AUC-ROC)
            if val_metrics['auc_roc'] > best_auc:
                best_auc = val_metrics['auc_roc']
                torch.save(model.state_dict(), ckpt_path)
                # Tag path only — avoids copying the .pt into mlruns (too large for git)
                mlflow.set_tag('best_checkpoint_path', str(ckpt_path))
                print(f"  ✓ best model saved (AUC={best_auc:.4f})")

        # Log final best metrics
        mlflow.log_metrics({'best_auc_roc': best_auc})
        print(f"\n[train] done — best AUC-ROC: {best_auc:.4f}")
        print(f"[train] checkpoint: {ckpt_path}")

    return best_auc


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='DermaVision training script')
    parser.add_argument('--exp_name',          type=str,   required=True)
    parser.add_argument('--backbone',          type=str,   default='efficientnet_b3')
    parser.add_argument('--epochs',            type=int,   default=NUM_EPOCHS)
    parser.add_argument('--batch_size',        type=int,   default=BATCH_SIZE)
    parser.add_argument('--lr',                type=float, default=LR)
    parser.add_argument('--weight_decay',      type=float, default=WEIGHT_DECAY)
    parser.add_argument('--dropout',           type=float, default=0.3)
    parser.add_argument('--scheduler',         type=str,   default='cosine',
                        choices=['cosine', 'step', 'none'])
    parser.add_argument('--use_class_weights', action='store_true')
    parser.add_argument('--use_mixup',         action='store_true')
    parser.add_argument('--mixup_alpha',       type=float, default=0.4)
    parser.add_argument('--use_advanced_aug',  action='store_true')
    parser.add_argument('--seed',              type=int,   default=SEED)
    parser.add_argument('--resume_ckpt',       type=str,   default=None)
    args = parser.parse_args()

    train(**vars(args))
