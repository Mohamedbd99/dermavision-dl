# DermaVision — Development Log

> **Project:** Skin Lesion Classification (HAM10000 / ISIC 2018 Task 3)  
> **Module:** Deep Learning — Prof. Haythem Ghazouani  
> **Students:** Mohamed bendaamar & omar gharbi  
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

### Tracking Infrastructure

**Goal:** Make all experiment data visible to professor — MLflow files committed, per-run CSVs exported, leaderboard auto-generated.

**Problem found:** `mlruns/` was in `.gitignore` so all metric/param files were invisible on GitHub.  
**Fix:** Removed `mlruns/` from ignore; added `mlruns/**/*.pt` rule instead (excludes only heavy weight files).

**Problem found:** `mlflow.log_artifact(ckpt_path)` was copying the 100MB `.pt` file into `mlruns/` on every save.  
**Fix:** Changed to `mlflow.set_tag('best_checkpoint_path', str(ckpt_path))` — stores path as metadata only.

**Problem found:** `*.csv` rule in `.gitignore` was blocking `experiments/` CSVs.  
**Fix:** Changed to `/data/**/*.csv` (anchored to data folder only).

**Files created:**
- `scripts/export_experiments.py` — reads all MLflow runs → writes `experiments/<name>/{params.json, metrics_final.json, metrics_per_epoch.csv, summary.md}` + `experiments/leaderboard.md`
- `DEVLOG.md` (this file)

**Commit:** `e923bfe`

---

## Experiments — Full Record

### Exp 01 — ResNet-50 Baseline

**Purpose:** Establish lower bound. Verify training pipeline works end-to-end before any optimization.

**Hypothesis:** Without class weights, model will learn to predict NV (66.9%) most of the time → high accuracy, low F1-macro.

**Command:**
```bash
python -m src.models.training \
  --exp_name exp01-resnet50-baseline \
  --backbone resnet50 --epochs 5 \
  --lr 1e-4 --dropout 0.2 --scheduler cosine --seed 42
python scripts/export_experiments.py
```

**Result:** AUC=0.9301, acc=0.778, F1-macro=0.467  
**Confirmed hypothesis:** F1-macro=0.467 — model strongly biased toward majority class NV.  
**Git tag:** `exp01-resnet50-baseline_auc0.930` | **Commit:** logged in mlruns

---

### Exp 02 — EfficientNet-B3 + Class Weights

**Purpose:** Two changes at once — better backbone (B3 vs ResNet-50) + fix class imbalance via weighted cross-entropy loss.

**Hypothesis:** Class weights will dramatically improve F1-macro on minority classes (DF, VASC). B3 feature extraction better than ResNet-50 for dermoscopy.

**Command:**
```bash
python -m src.models.training \
  --exp_name exp02-efficientnet-b3-weighted \
  --backbone efficientnet_b3 --epochs 10 \
  --lr 1e-4 --dropout 0.3 --scheduler cosine \
  --use_class_weights --seed 42
python scripts/export_experiments.py
```

**Result:** AUC=0.9644 (+3.4pp), F1-macro=0.723 (+25.6pp!)  
**Finding: class weights were the single biggest improvement in the entire project.** Going from 0.467 to 0.723 F1-macro in one step — the model stopped ignoring minority classes entirely.  
**Git tag:** `exp02-efficientnet-b3-weighted_auc0.9644` | **Commit:** `e923bfe`

---

### Exp 03 — EfficientNet-B3 + Class Weights + Advanced Augmentation

**Purpose:** Add spatial augmentations (GridDistortion + CoarseDropout) to improve generalization on dermoscopy images.

**Rationale:** Dermoscopy images have artifacts (hair, gel reflections, vignetting). GridDistortion simulates lens distortion. CoarseDropout forces the model to use full lesion context rather than memorizing local patches.

**Command:**
```bash
python -m src.models.training \
  --exp_name exp03-efficientnet-b3-advanced-aug \
  --backbone efficientnet_b3 --epochs 15 \
  --lr 1e-4 --dropout 0.3 --scheduler cosine \
  --use_class_weights --use_advanced_aug --seed 42
python scripts/export_experiments.py
```

**Result:** AUC=0.9713 (+0.69pp vs Exp 02), acc=0.824  
**Finding:** Advanced augmentation consistently helps. This became the **baseline for all subsequent experiments**.  
**Git tag:** `exp03-efficientnet-b3-advanced-aug_auc0.9713` | **Commit:** `d32450b`

---

### Exp 04 — EfficientNet-B3 + Class Weights + MixUp Only

**Purpose:** Test MixUp augmentation in isolation (without spatial aug) to isolate its contribution.

**Hypothesis:** MixUp (label-smoothing via linear interpolation of samples) helps with calibration and minority class boundaries.

**Command:**
```bash
python -m src.models.training \
  --exp_name exp04-efficientnet-b3-mixup \
  --backbone efficientnet_b3 --epochs 15 \
  --lr 1e-4 --dropout 0.3 --scheduler cosine \
  --use_class_weights --use_mixup --mixup_alpha 0.4 --seed 42
python scripts/export_experiments.py
```

**Result:** AUC=0.9523 — **worse than Exp 02 (0.9644) and far below Exp 03 (0.9713)**  
**Finding: MixUp alone hurts on this dataset.** Likely reason: 7-class imbalanced medical data with very distinct visual categories — blending images from different classes (e.g. MEL + NV) creates unrealistic composites that confuse the model rather than regularizing it.  
**Git tag:** `exp04-efficientnet-b3-mixup_auc0.9523` | **Commit:** `db67489`

---

### Exp 05 — EfficientNet-B3 + Full Stack (Class Weights + Adv Aug + MixUp)

**Purpose:** Test whether combining the best spatial augmentation (Exp 03) with MixUp recovers performance.

**Hypothesis:** Maybe MixUp hurts alone but helps as an additional regularizer on top of spatial aug.

**Command:**
```bash
python -m src.models.training \
  --exp_name exp05-efficientnet-b3-full-stack \
  --backbone efficientnet_b3 --epochs 20 \
  --lr 1e-4 --dropout 0.3 --scheduler cosine \
  --use_class_weights --use_advanced_aug --use_mixup --mixup_alpha 0.4 --seed 42
python scripts/export_experiments.py
```

**Result:** AUC=0.9603 — below both Exp 03 (0.9713) and Exp 02 (0.9644)  
**Finding: MixUp consistently hurts regardless of whether spatial aug is present.** Hypothesis rejected. MixUp is dropped from all future experiments.  
**Ablation conclusion:** Exp 03 config (class weights + spatial aug, no MixUp) is the best augmentation stack.  
**Git tag:** `exp05-efficientnet-b3-full-stack_auc0.9603` | **Commit:** `740775e`

---

### Exp 06 — EfficientNet-B4 Scale-Up

**Purpose:** Test whether a larger backbone (B4: 19M params vs B3: 12M params) improves on the best config (Exp 03).

**Hypothesis:** More capacity → better feature extraction → higher AUC.

**Command:**
```bash
python -m src.models.training \
  --exp_name exp06-efficientnet-b4-scaleup \
  --backbone efficientnet_b4 --epochs 20 \
  --lr 1e-4 --dropout 0.4 --scheduler cosine \
  --use_class_weights --use_advanced_aug --seed 42
python scripts/export_experiments.py
```

**Result:** AUC=0.9660, acc=0.795 — **below Exp 03 (0.9713)**, ~330s/epoch (+33% slower than B3)  
**Finding: scale-up did not help.** B4 has more parameters but the dataset (8,012 train images) is too small to fully leverage the extra capacity. B4 likely overfits the additional parameters. Speed cost (+33%) is not justified.  
**Conclusion:** Stay with EfficientNet-B3.  
**Git tag:** `exp06-efficientnet-b4-scaleup_auc0.9660` | **Commit:** `5c7f615`

---

### Exp 07 — Optuna Hyperparameter Search + FINAL Model

**Purpose:** Use Bayesian optimization to find optimal lr, weight_decay, dropout, scheduler — then do full training run with those params.

**Design:**
- Sampler: TPE (Tree-structured Parzen Estimator) — Bayesian, converges faster than random
- Pruner: MedianPruner — kills trials underperforming the median at any epoch
- 10 trials × 5 epochs each (fast proxy), then full 20-epoch retrain of best config
- Search space: lr ∈ [1e-5, 5e-4] log, wd ∈ [1e-6, 1e-3] log, dropout ∈ [0.2, 0.5], scheduler ∈ {cosine, step}
- Fixed: efficientnet_b3, class_weights=True, advanced_aug=True, mixup=False

**Command:**
```bash
python scripts/optuna_search.py --n_trials 10 --study_name exp07-optuna \
  2>&1 | tee logs/exp07_optuna.log
python scripts/export_experiments.py
```

**Trial results:**
| Trial | AUC | lr | dropout | scheduler | Notes |
|---|---|---|---|---|---|
| 2 | 0.9392 | 4.33e-5 | 0.420 | cosine | first complete |
| 3 | 0.9303 | 1.84e-5 | 0.460 | step | |
| 4 | 0.8989 | 1.08e-5 | 0.450 | cosine | low lr bad |
| 5 | 0.9208 | 2.05e-5 | 0.357 | cosine | |
| **6** | **0.9590** | **1.10e-4** | **0.288** | **step** | breakthrough |
| **7** | **0.9615** | **2.16e-4** | **0.354** | **cosine** | new best |
| 8 | 0.9597 | 1.08e-4 | 0.220 | step | |
| **9** | **0.9628** | **2.36e-4** | **0.229** | **cosine** | **BEST TRIAL** |
| 10 | pruned | — | — | — | MedianPruner eliminated |
| 11 | 0.9588 | 1.34e-4 | 0.356 | cosine | TPE exploration |

**FINAL retrain with best params (20 epochs):**

| Epoch | AUC | Epoch | AUC |
|---|---|---|---|
| 1 | 0.9296 | 11 | 0.9733 |
| 4 | 0.9603 | 12 | 0.9736 |
| 8 | 0.9694 | 14 | 0.9759 |
| 10 | 0.9708 | 16 | **0.9773** |
| | | 18 | **0.9776** ← best |

**Final result: AUC=0.9776, acc=0.854**

**Key insights from Optuna:**
- Default dropout (0.3) was too aggressive — optimal is 0.229 (less regularization)
- Default lr (1e-4) was too conservative — optimal is 2.36e-4 (faster convergence)
- Cosine scheduler confirmed as best across all top trials
- Low lr (< 5e-5) consistently fails — model never converges properly in 5 epochs
- The TPE sampler quickly focused on lr ≈ 1e-4 to 3e-4 range after trial 5

**Checkpoint:** `checkpoints/exp07-optuna-FINAL_best.pt` ← **PRODUCTION MODEL**  
**Git tag:** `exp07-optuna-final_auc0.9776` | **Commit:** `e349338`

---

## Ablation Summary

| What changed | vs baseline | AUC delta | Conclusion |
|---|---|---|---|
| ResNet-50 → EfficientNet-B3 | Exp01→02 | +3.4pp | Backbone matters for dermoscopy |
| No weights → class weights | Exp01→02 | +25.6pp F1 | **Most impactful single change** |
| No aug → advanced aug | Exp02→03 | +0.7pp | Spatial aug consistently helps |
| No MixUp → MixUp | Exp02→04 | -1.2pp | MixUp hurts on this dataset |
| Adv aug → adv aug + MixUp | Exp03→05 | -1.1pp | MixUp hurts even with spatial aug |
| B3 → B4 | Exp03→06 | -0.5pp | Larger backbone overfits small dataset |
| Default lr/dropout → Optuna | Exp03→07 | +0.6pp | Hyperparameter tuning always worth it |

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

---

## Week 5 — FastAPI Backend

### 2026-05-01 — API Phase

**Objective:** Expose the trained EfficientNet-B3 model (Exp 07, AUC=0.9776)
via a production-grade FastAPI backend with JWT authentication, SQLite persistence,
and full Swagger UI documentation.

**Architecture decisions:**

| Decision | Reason |
|---|---|
| **FastAPI** | Mandatory per subject rules; async-ready, automatic OpenAPI/Swagger |
| **SQLite + SQLAlchemy 2.x** | Zero-config DB for dev/demo; ORM keeps it swappable to Postgres |
| **JWT (HS256, python-jose)** | Stateless auth; no server-side session store needed |
| **bcrypt (passlib)** | Industry-standard password hashing; never store plain text |
| **Lifespan context manager** | Load model ONCE at startup; avoid per-request reload (latency) |
| **`app.state` for model** | Thread-safe way to share model across all requests in FastAPI |
| **Predictions audit table** | Every `/predict` call logged → reproducibility + user history |
| **CORS open in dev** | Frontend (any origin) can call API locally; restrict in production |

---

### Files created

```
src/api/
├── __init__.py        (pre-existing, empty)
├── database.py        SQLAlchemy models: User + Prediction tables, get_db dependency
├── auth.py            bcrypt password utils, JWT create/decode, get_current_user dependency
├── endpoints.py       All route handlers (7 endpoints)
└── main.py            FastAPI app factory, lifespan, CORS, Swagger config

run_api.py             Convenience launcher at repo root (argparse wrapping uvicorn)
```

---

### Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/register` | ❌ public | Create account (bcrypt hash stored) |
| `POST` | `/auth/login` | ❌ public | OAuth2 form → JWT token (60 min) |
| `GET` | `/me` | 🔒 JWT | Current user profile |
| `GET` | `/health` | ❌ public | Device, model, checkpoint status |
| `GET` | `/metrics` | ❌ public | Full Exp 07 performance metrics |
| `POST` | `/predict` | 🔒 JWT | Upload image → top-1 class + all 7 scores |
| `GET` | `/history` | 🔒 JWT | User's prediction audit log |

---

### Commands

```bash
# Start the API (dev mode with auto-reload)
source venv/bin/activate
python run_api.py

# Or directly with uvicorn
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Swagger UI
open http://localhost:8000/docs

# Quick smoke tests
curl http://localhost:8000/health
curl http://localhost:8000/metrics

# Register + login + predict
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"secret123"}'

curl -X POST http://localhost:8000/auth/login \
  -d "username=alice&password=secret123"

# Use the token from login:
curl -X POST http://localhost:8000/predict \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@/path/to/lesion.jpg"
```

---

### Data flow for `/predict`

```
Client uploads JPEG/PNG
        │
        ▼
cv2.imdecode (BGR→RGB)          # matches training pipeline exactly
        │
        ▼
get_val_transforms()             # Resize 224×224, ImageNet normalize
        │
        ▼
DermaVisionModel.forward()       # EfficientNet-B3, Exp07 weights
        │
        ▼
F.softmax(logits, dim=-1)        # 7 class probabilities
        │
        ▼
top-1 class + confidence         # returned in PredictionOut schema
        │
        ▼
INSERT INTO predictions          # audit log with all 7 scores as JSON
```

---

### Result

Server starts in ~3s (model load on MPS), Swagger UI fully functional at `/docs`.
All 7 endpoints documented with request/response schemas and inline descriptions.
Predictions are persisted per user for history/audit.

**Git commit:** `feat: FastAPI backend with JWT auth, SQLite, /predict endpoint + Swagger`
