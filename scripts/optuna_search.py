"""
scripts/optuna_search.py
========================
Optuna hyperparameter search for DermaVision.

Search space (based on ablation findings from Exp 01–06):
  - lr             : loguniform [1e-5, 5e-4]
  - weight_decay   : loguniform [1e-6, 1e-3]
  - dropout        : uniform [0.2, 0.5]
  - scheduler      : categorical ['cosine', 'step']
  - backbone       : categorical ['efficientnet_b3', 'efficientnet_b4']

Fixed (proven from ablations):
  - use_class_weights = True   (Exp 02 +25pp F1)
  - use_advanced_aug  = True   (Exp 03 best AUC)
  - use_mixup         = False  (Exp 04/05: MixUp hurts)
  - epochs per trial  = 10     (fast proxy; best config gets 25 epochs)

Usage:
    python scripts/optuna_search.py --n_trials 20
    python scripts/optuna_search.py --n_trials 20 --study_name exp07-optuna
"""

import argparse
import sys
from pathlib import Path

import optuna
import mlflow
import torch
import numpy as np
from torch.utils.data import DataLoader

# Repo root on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils.config import (
    REPO_ROOT, IMAGES_DIR, CLASS_NAMES, BATCH_SIZE, SEED, NUM_WORKERS
)
from src.data.dataset import build_dataframes, HAM10000Dataset
from src.data.preprocessing import get_train_transforms, get_val_transforms
from src.models.architecture import DermaVisionModel
from src.models.training import (
    _seed_everything, _get_device, _compute_class_weights,
    _train_epoch, _val_epoch,
)

MLRUNS_DIR = REPO_ROOT / 'mlruns'
CKPT_DIR   = REPO_ROOT / 'checkpoints'

TRIAL_EPOCHS = 5     # fast proxy (MPS: ~15 min/trial → 10 trials ≈ 2.5 hrs)
FINAL_EPOCHS = 20    # retrain best config


def objective(trial: optuna.Trial) -> float:
    """Single Optuna trial — returns best val AUC-ROC."""
    # ── Sample hyperparameters ───────────────────────────────────────
    backbone     = 'efficientnet_b3'   # fixed: best from ablation (Exp03)
    lr           = trial.suggest_float('lr', 1e-5, 5e-4, log=True)
    weight_decay = trial.suggest_float('weight_decay', 1e-6, 1e-3, log=True)
    dropout      = trial.suggest_float('dropout', 0.2, 0.5)
    scheduler    = trial.suggest_categorical('scheduler', ['cosine', 'step'])

    _seed_everything(SEED)
    device = _get_device()

    # ── Data ─────────────────────────────────────────────────────────
    train_df, val_df = build_dataframes(seed=SEED)
    train_ds = HAM10000Dataset(train_df, IMAGES_DIR,
                               transform=get_train_transforms(use_advanced_aug=True))
    val_ds   = HAM10000Dataset(val_df, IMAGES_DIR, transform=get_val_transforms())
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,
                              num_workers=NUM_WORKERS, pin_memory=True, drop_last=True)
    val_loader   = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False,
                              num_workers=NUM_WORKERS, pin_memory=True)

    # ── Model ─────────────────────────────────────────────────────────
    model = DermaVisionModel(backbone=backbone, dropout=dropout).to(device)
    cw    = _compute_class_weights(train_df, len(CLASS_NAMES)).to(device)
    criterion = torch.nn.CrossEntropyLoss(weight=cw)
    optimizer = torch.optim.AdamW(
        model.get_param_groups(base_lr=lr, head_lr_multiplier=10.0),
        weight_decay=weight_decay
    )
    sched = (torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=TRIAL_EPOCHS, eta_min=1e-6)
             if scheduler == 'cosine'
             else torch.optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.1))

    best_auc = 0.0
    for epoch in range(1, TRIAL_EPOCHS + 1):
        _train_epoch(model, train_loader, optimizer, criterion, device)
        val_m = _val_epoch(model, val_loader, criterion, device)
        sched.step()
        if val_m['auc_roc'] > best_auc:
            best_auc = val_m['auc_roc']

        # Pruning: stop unpromising trials early
        trial.report(best_auc, epoch)
        if trial.should_prune():
            raise optuna.exceptions.TrialPruned()

    return best_auc


def run_search(n_trials: int = 20, study_name: str = 'exp07-optuna'):
    """Run Optuna study and log best config to MLflow."""
    storage_path = str(REPO_ROOT / 'optuna_study.db')

    sampler = optuna.samplers.TPESampler(seed=SEED)
    pruner  = optuna.pruners.MedianPruner(n_startup_trials=5, n_warmup_steps=3)

    study = optuna.create_study(
        study_name=study_name,
        direction='maximize',
        sampler=sampler,
        pruner=pruner,
        storage=f'sqlite:///{storage_path}',
        load_if_exists=True,
    )

    print(f"[optuna] Starting study '{study_name}' — {n_trials} trials")
    print(f"[optuna] Each trial = {TRIAL_EPOCHS} epochs (fast proxy)")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

    best = study.best_trial
    print(f"\n[optuna] Best trial #{best.number}: AUC={best.value:.4f}")
    print(f"[optuna] Best params: {best.params}")

    # ── Log best params to MLflow ─────────────────────────────────────
    mlflow.set_tracking_uri(str(MLRUNS_DIR))
    mlflow.set_experiment(study_name)
    with mlflow.start_run(run_name=f"{study_name}-best-config"):
        mlflow.log_params({**best.params, 'backbone': 'efficientnet_b3',
                           'n_trials': n_trials,
                           'trial_epochs': TRIAL_EPOCHS})
        mlflow.log_metric('best_trial_auc', best.value)

    # ── Retrain best config for full FINAL_EPOCHS ─────────────────────
    print(f"\n[optuna] Retraining best config for {FINAL_EPOCHS} epochs...")
    from src.models.training import train
    final_auc = train(
        exp_name=f"{study_name}-FINAL",
        backbone='efficientnet_b3',
        epochs=FINAL_EPOCHS,
        lr=best.params['lr'],
        weight_decay=best.params['weight_decay'],
        dropout=best.params['dropout'],
        scheduler=best.params['scheduler'],
        use_class_weights=True,
        use_advanced_aug=True,
        use_mixup=False,
        seed=SEED,
        mlflow_uri=str(MLRUNS_DIR),
    )

    print(f"\n[optuna] FINAL model AUC-ROC: {final_auc:.4f}")
    print(f"[optuna] Checkpoint: checkpoints/{study_name}-FINAL_best.pt")
    return best.params, final_auc


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--n_trials',   type=int, default=10)
    parser.add_argument('--study_name', type=str, default='exp07-optuna')
    args = parser.parse_args()
    run_search(args.n_trials, args.study_name)
