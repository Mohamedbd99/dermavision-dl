# DermaVision — Development Log

> **Project:** Skin Lesion Classification (HAM10000 / ISIC 2018 Task 3)  
> **Module:** Deep Learning — Prof. Haythem Ghazouani  
> **Student:** Mohamed bendaamar & omar gharbi  
> **Repo:** https://github.com/Mohamedbd99/dermavision-dl  
> **Dataset:** ISIC 2018 Task 3 — 10,015 dermoscopy images, 7 classes  

This file is the **single source of truth** for every decision, command, and finding made during the project. Updated after every significant step.

---

## Table of Contents

1. [Week 1 — Setup & EDA](#week-1--setup--eda)
2. [Week 2 — Data Pipeline](#week-2--data-pipeline)
3. [Week 3 — Models & Experiments](#week-3--models--experiments)
4. [Experiment Results Summary](#experiment-results-summary)
5. [Architecture Decisions](#architecture-decisions)
6. [Known Issues & Fixes](#known-issues--fixes)

---

## Week 1 — Setup & EDA

### Day 1 · Project Initialization

**Goal:** Choose topic, set up repo, install environment.

**Decisions:**
- Dataset: **HAM10000 / ISIC 2018 Task 3** — 10,015 images, 7 classes, real-world clinical imbalance
- Stack: PyTorch + timm + FastAPI + React/TypeScript + MLflow + Docker
- Primary metric: **AUC-ROC (macro OvR)** — robust to class imbalance (accuracy is misleading here)
- Backbone: **EfficientNet-B3** (good accuracy/params tradeoff for medical imaging)

**Commands executed:**
```bash
# Initialize git repo
cd /Users/bidoun/Documents/projet_fed
git init
git remote add origin https://github.com/Mohamedbd99/dermavision-dl.git

# Create Python venv
python3 -m venv venv
source venv/bin/activate

# Install all dependencies
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install timm albumentations opencv-python-headless scikit-learn
pip install mlflow optuna fastapi uvicorn python-jose passlib bcrypt sqlalchemy
pip install pandas numpy matplotlib seaborn Pillow ipykernel ipywidgets
pip install pytest pytest-cov black isort

# Create full project scaffold
mkdir -p src/{utils,data,models,api} tests notebooks scripts data checkpoints

# Download dataset (Kaggle API failed — token format issue)
# Bypassed with direct ISIC S3 URL:
curl -L "https://isic-challenge-data.s3.amazonaws.com/2018/ISIC2018_Task3_Training_Input.zip" \
     -o data/HAM10000/images.zip
curl -L "https://isic-challenge-data.s3.amazonaws.com/2018/ISIC2018_Task3_Training_GroundTruth.zip" \
     -o data/HAM10000/labels.zip
cd data/HAM10000 && unzip images.zip && unzip labels.zip && cd ../..
```

**Findings:** Kaggle API token format `KGAT_...` is incompatible with the CLI's username+key JSON format. Direct S3 URLs worked without authentication.

**Commit:** `daa1853` — Initial scaffold

---

### Day 2 · EDA Notebook

**Goal:** Understand dataset — class distribution, image quality, class separability.

**File:** `notebooks/01_data_exploration.ipynb`

**Commands:**
```bash
# Run EDA notebook cell by cell (verified before committing)
# Fixed path issue: initial hardcoded Path('../data/HAM10000') → dynamic NOTEBOOK_DIR.parent
# CSV format: ISIC uses one-hot columns, not a 'dx' column like HAM10000 metadata
# Fixed with: df[label_cols].idxmax(axis=1)

git add notebooks/01_data_exploration.ipynb
git commit -m "feat: EDA notebook fully tested — 10015 samples, class weights, t-SNE, quality analysis"
git push
```

**Key findings from EDA:**

| Finding | Impact on Training |
|---|---|
| **NV = 66.9%** of dataset | Accuracy is misleading — use AUC-ROC |
| All images **600×450 px**, 0 corrupt | Uniform resize to 224×224 — no special handling |
| Colour features **overlap in t-SNE** | Transfer learning justified — shallow features insufficient |
| DF weight **12.44×**, NV weight **0.21×** | Weighted cross-entropy loss mandatory |

**Commit:** `10f4a77`

---

## Week 2 — Data Pipeline

### src/utils/config.py

**Purpose:** Single source of truth for all paths, label maps, and training defaults.

**Key constants:**
- `REPO_ROOT = Path(__file__).resolve().parents[2]` — dynamic, works from any CWD
- `CLASS_NAMES = sorted(LABEL_COLS)` → `['AKIEC','BCC','BKL','DF','MEL','NV','VASC']` — **alphabetical order = label indices**
- `IMG_SIZE = 224`, `BATCH_SIZE = 32`, `LR = 1e-4`, `VAL_SPLIT = 0.2`, `SEED = 42`

**Bug fixed:** `.gitignore` had `data/` which matched `src/data/` — changed to `/data/` (anchored to repo root).

---

### src/utils/metrics.py

**Purpose:** `compute_metrics(y_true, y_pred, y_prob) → dict`

**Metrics computed:**
- `accuracy` — simple correct/total
- `auc_roc` — `roc_auc_score(..., multi_class='ovr', average='macro')`
- `f1_macro`, `f1_weighted` — from sklearn
- `sensitivity` — macro-average of per-class TP/(TP+FN) from confusion matrix
- `specificity` — macro-average of per-class TN/(TN+FP) from confusion matrix

---

### src/data/dataset.py

**Purpose:** `HAM10000Dataset` + `build_dataframes()`

**Design:**
- `build_dataframes()` reads the one-hot CSV, decodes via `idxmax`, does stratified 80/20 split
- `HAM10000Dataset.__getitem__` loads with OpenCV (BGR→RGB), applies albumentations transform, returns `(tensor, int)`
- Label indices follow `CLASS_NAMES` (alphabetical), consistent with config

**Sanity check result:** 8,012 train / 2,003 val, stratified across all 7 classes

---

### src/data/preprocessing.py

**Purpose:** Albumentations augmentation pipelines

**Pipelines:**
- `get_train_transforms()` — Resize + HFlip + VFlip + Rotate + ColorJitter + RandomCrop + ImageNet normalize
- `get_train_transforms(use_advanced_aug=True)` — adds GridDistortion + CoarseDropout (Exp 06+)
- `get_val_transforms()` — Resize + normalize only (deterministic)
- `mixup_batch()` / `mixup_criterion()` — MixUp data augmentation helpers (Exp 04+)

**Commands:**
```bash
# Sanity check all 4 modules
python - << 'EOF'
# ... ran config, metrics, preprocessing, dataset checks
# Verified: batch shape (8, 3, 224, 224), stratified split, label indices
EOF

git add .gitignore src/utils/config.py src/utils/metrics.py src/data/dataset.py src/data/preprocessing.py
git commit -m "feat: data pipeline — config, metrics, dataset, preprocessing"
git push
```

**Commit:** `7572eec`

---

## Week 3 — Models & Experiments

### src/models/architecture.py

**Purpose:** Flexible `DermaVisionModel` wrapping any timm backbone.

**Design:**
- `timm.create_model(backbone, pretrained=True, num_classes=0, global_pool='avg')` — removes original head
- Custom head: `Dropout(p) → Linear(in_features, 7)`
- `freeze_base()` / `unfreeze_base()` — for two-phase training
- `get_param_groups(base_lr, head_lr_multiplier=10)` — head gets 10× learning rate

**Factory functions:**
- `build_baseline_cnn()` → ResNet-50, dropout=0.2 (Exp 01)
- `build_efficientnet_b3()` → EfficientNet-B3, dropout=0.3 (Exp 02+)
- `build_efficientnet_b4()` → EfficientNet-B4, dropout=0.4 (Exp 07)

---

### src/models/training.py

**Purpose:** Full training loop with MLflow logging, CLI entry point.

**Features:**
- Auto-detect device: MPS (Apple Silicon) → CUDA → CPU
- Inverse-frequency class weights, normalized to sum = NUM_CLASSES
- AdamW optimizer with differential LRs (backbone vs head)
- Scheduler: cosine annealing / step decay / none
- MixUp support via `--use_mixup` flag
- Best checkpoint saved by AUC-ROC to `checkpoints/<exp_name>_best.pt`
- All params + per-epoch metrics logged to MLflow

**CLI usage:**
```bash
python -m src.models.training \
  --exp_name "exp02-efficientnet-b3-weighted" \
  --backbone efficientnet_b3 \
  --epochs 10 \
  --use_class_weights \
  --scheduler cosine \
  --seed 42
```

**Commands:**
```bash
# Sanity check architecture + training module
python - << 'EOF'
# ... tested: resnet50 (4,7) ✓  efficientnet_b3 (4,7) ✓
# ... tested: param_groups, freeze/unfreeze, val_epoch dict
EOF

git add src/models/architecture.py src/models/training.py
git commit -m "feat: model architecture + training loop"
git push
```

**Commit:** `2208c03`

---

## Experiment Results Summary

> Full details in [experiments/leaderboard.md](experiments/leaderboard.md)  
> Per-epoch CSVs in `experiments/<exp_name>/metrics_per_epoch.csv`

| # | Experiment | Backbone | Epochs | AUC-ROC | Accuracy | F1-macro | vs Baseline |
|---|---|---|---|---|---|---|---|
| 1 | exp02-efficientnet-b3-weighted | EfficientNet-B3 | 10 | **0.9644** | 0.811 | 0.723 | +3.4pp |
| 2 | exp01-resnet50-baseline | ResNet-50 | 5 | 0.9301 | 0.778 | 0.467 | — |

### Exp 01 — ResNet-50 Baseline (`exp01-resnet50-baseline`)

**Purpose:** Establish lower bound. No class weights, no fancy augmentation.  
**Command:**
```bash
python -m src.models.training \
  --exp_name "exp01-resnet50-baseline" --backbone resnet50 \
  --epochs 5 --lr 1e-4 --dropout 0.2 --scheduler cosine --seed 42
```
**Result:** AUC=0.9301, acc=0.778 — good baseline but F1-macro=0.467 reveals poor minority class handling  
**Git tag:** `exp01-resnet50-baseline_auc0.930`

---

### Exp 02 — EfficientNet-B3 + Class Weights (`exp02-efficientnet-b3-weighted`)

**Purpose:** Upgrade backbone + fix imbalance with weighted loss.  
**Command:**
```bash
python -m src.models.training \
  --exp_name "exp02-efficientnet-b3-weighted" --backbone efficientnet_b3 \
  --epochs 10 --lr 1e-4 --dropout 0.3 --scheduler cosine \
  --use_class_weights --seed 42
```
**Result:** AUC=0.9644 (+3.4pp), F1-macro=0.723 (+25.6pp!) — class weights made the biggest difference  
**Git tag:** `exp02-efficientnet-b3-weighted_auc0.9644`

---

## Architecture Decisions

| Decision | Reason |
|---|---|
| **EfficientNet-B3 as main backbone** | Best acc/params ratio for medical imaging; timm provides pretrained weights |
| **ImageNet pretrained weights** | Transfer learning critical for small medical datasets |
| **Differential LRs** (backbone 1e-4, head 1e-3) | Head needs to learn fast; backbone already pretrained |
| **Cosine annealing scheduler** | Smooth decay, avoids oscillation near convergence |
| **AdamW over Adam** | Weight decay decoupled — better generalization |
| **Albumentations over torchvision** | Faster, richer medical augmentation options |
| **AUC-ROC as primary metric** | Robust to class imbalance; clinically meaningful |
| **Stratified 80/20 split** | Ensures all 7 classes represented in validation |

---

## Known Issues & Fixes

| Issue | Fix Applied |
|---|---|
| `data/` in `.gitignore` blocked `src/data/` | Changed `data/` → `/data/` (anchored glob) |
| Kaggle API `KGAT_` token incompatible | Downloaded directly from ISIC S3 URLs |
| `mlflow.log_artifact` copied 100MB `.pt` into mlruns | Changed to `mlflow.set_tag('best_checkpoint_path', ...)` |
| Notebook file wiped to 0 bytes by edit tool | Recovered with `cat > file << 'NBEOF'` heredoc |
| ISIC CSV is one-hot (no `dx` column) | Used `df[label_cols].idxmax(axis=1)` |
| `mlruns/` gitignored → professor couldn't see metrics | Removed from `.gitignore`; only `mlruns/**/*.pt` excluded |
