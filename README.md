# DermaVision DL

Multi-class skin lesion classification using deep learning on the **HAM10000 / ISIC 2018** dataset.

> **Stack:** PyTorch · EfficientNet-B3 · FastAPI · React + TypeScript · MLflow · Optuna · Docker · PostgreSQL
> **Module:** Deep Learning — Prof. Haythem Ghazouani
> **Students:** Mohamed Bendaamar & Omar Gharbi

---

## 🚀 Quickstart — zero dependencies required

```bash
git clone https://github.com/Mohamedbd99/dermavision-dl.git
cd dermavision-dl
docker compose up --build
```

Open **http://localhost:3000** — that's it.

**What happens automatically:**
- `db` — PostgreSQL 16 starts and becomes healthy
- `api` — model checkpoint is downloaded from GitHub Releases, tables are created, FastAPI starts
- `frontend` — React app is built and served via nginx

**No `.env` file needed.** All defaults are wired in `docker-compose.yml`.  
Optional: copy `.env.example` → `.env` if you want a custom `SECRET_KEY` for production.

---

## Results

| Experiment | Model | AUC-ROC | Accuracy | F1-macro |
|---|---|---|---|---|
| **Exp 07 — Optuna FINAL** | EfficientNet-B3 | **0.9776** | 0.854 | 0.796 |
| Exp 03 — Advanced Aug | EfficientNet-B3 | 0.9713 | 0.824 | 0.772 |
| Exp 06 — B4 Scale-Up | EfficientNet-B4 | 0.9660 | 0.795 | 0.711 |
| Exp 02 — Class Weights | EfficientNet-B3 | 0.9644 | 0.811 | 0.723 |
| Exp 01 — ResNet-50 Baseline | ResNet-50 | 0.9301 | 0.778 | 0.467 |

Full leaderboard: [`experiments/leaderboard.md`](experiments/leaderboard.md)
Per-epoch CSVs + params: [`experiments/`](experiments/)
MLflow runs: committed in [`mlruns/`](mlruns/) (text files only, weights excluded)

---

## Project Overview

**Dataset:** HAM10000 — 10,015 dermoscopic images, 7 lesion classes (AKIEC, BCC, BKL, DF, MEL, NV, VASC), severe imbalance (NV = 66.9%)
**Task:** Multi-class classification
**Primary metric:** AUC-ROC (macro OvR) — chosen because accuracy is misleading under 66.9% class imbalance
**Split:** Stratified 80/20 → 8,012 train / 2,003 val

**Key findings from ablation study (Exp 01–07):**
- Class-weighted loss: +25.6pp F1-macro (most impactful single change)
- GridDistortion + CoarseDropout augmentation: +0.7pp AUC
- MixUp: consistently hurts on this dataset (−1.2pp AUC)
- EfficientNet-B4 vs B3: B4 performs worse (overfits small dataset, +33% slower)
- Optuna hyperparameter search (lr=2.36e-4, dropout=0.229): +0.6pp AUC

---

## Setup

### Prerequisites
- Python 3.9+
- Dataset: ISIC 2018 Task 3 (download separately — see below)

### Install

```bash
git clone https://github.com/Mohamedbd99/dermavision-dl.git
cd dermavision-dl
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Dataset

Download from ISIC S3 (no authentication required):
```bash
mkdir -p data/HAM10000
curl -L "https://isic-challenge-data.s3.amazonaws.com/2018/ISIC2018_Task3_Training_Input.zip" \
  -o data/HAM10000/images.zip
curl -L "https://isic-challenge-data.s3.amazonaws.com/2018/ISIC2018_Task3_Training_GroundTruth.zip" \
  -o data/HAM10000/labels.zip
cd data/HAM10000 && unzip images.zip && unzip labels.zip && cd ../..
```

Expected structure:
```
data/HAM10000/
├── ISIC2018_Task3_Training_Input/      # 10,015 .jpg images
└── ISIC2018_Task3_Training_GroundTruth.csv
```

---

## Training

### Run any experiment
```bash
source venv/bin/activate
python -m src.models.training \
  --exp_name my-experiment \
  --backbone efficientnet_b3 \
  --epochs 20 \
  --lr 2.36e-4 \
  --dropout 0.229 \
  --weight_decay 8.2e-6 \
  --scheduler cosine \
  --use_class_weights \
  --use_advanced_aug \
  --seed 42
```

### Reproduce best model (Exp 07 Optuna config)
```bash
python -m src.models.training \
  --exp_name exp07-optuna-FINAL \
  --backbone efficientnet_b3 --epochs 20 \
  --lr 2.36e-4 --dropout 0.229 --weight_decay 8.2e-6 \
  --scheduler cosine --use_class_weights --use_advanced_aug --seed 42
```

### Run Optuna hyperparameter search
```bash
python scripts/optuna_search.py --n_trials 10 --study_name my-optuna-search
```

### Export experiments to readable files
```bash
python scripts/export_experiments.py
# writes experiments/<name>/{params.json, metrics_final.json, metrics_per_epoch.csv, summary.md}
# writes experiments/leaderboard.md
```

### View MLflow UI
```bash
mlflow ui --backend-store-uri mlruns/
# http://localhost:5000
```

---

## Project Structure

```
dermavision-dl/
├── src/
│   ├── utils/
│   │   ├── config.py           # All paths, constants, hyperparameter defaults
│   │   └── metrics.py          # AUC-ROC, F1, sensitivity, specificity
│   ├── data/
│   │   ├── dataset.py          # HAM10000Dataset + build_dataframes()
│   │   └── preprocessing.py    # Albumentations pipelines + MixUp helpers
│   ├── models/
│   │   ├── architecture.py     # DermaVisionModel (timm backbone + custom head)
│   │   └── training.py         # Full training loop + MLflow logging + CLI
│   └── api/                    # FastAPI backend (in progress)
├── scripts/
│   ├── export_experiments.py   # MLflow → experiments/ folder
│   └── optuna_search.py        # Bayesian hyperparameter search
├── experiments/                # Auto-generated per-run results + leaderboard
├── mlruns/                     # MLflow tracking data (committed, weights excluded)
├── checkpoints/                # Best model weights (gitignored)
├── notebooks/
│   └── 01_data_exploration.ipynb
└── data/                       # Dataset (gitignored — download separately)
```

---

## Troubleshooting

### Docker — `dial tcp: lookup registry-1.docker.io: no such host` / `i/o timeout`

Docker Desktop cannot reach Docker Hub to pull base images. This is a DNS issue on macOS.

**Fix (permanent):**

1. Open **Docker Desktop → Settings → Docker Engine** and add:
   ```json
   {
     "dns": ["8.8.8.8", "8.8.4.4"]
   }
   ```
2. Click **Apply & Restart**.
3. Re-run `docker compose up --build`.

**Alternative (no settings change):** pre-pull the images manually while connected to a working network, then build offline:
```bash
docker pull python:3.9-slim
docker pull node:18-alpine
docker pull nginx:1.25-alpine
docker compose up --build
```

> **Root cause:** Docker Desktop loses its DNS resolver after network switches or sleep/wake cycles. Using Google DNS (`8.8.8.8`) bypasses the broken system resolver.

---

### `docker compose up` — `version` attribute warning

```
the attribute `version` is obsolete, it will be ignored
```
Harmless — newer versions of Compose no longer need the `version:` field. Safe to ignore.

---

### API container — model checkpoint not found

The `.pt` weight files are git-ignored (too large). On a fresh clone you must either:
- Copy `checkpoints/exp07-optuna-FINAL_best.pt` onto the machine, **or**
- Download it from the GitHub Release attached to this repo (see Releases tab).

---

## Ethical Considerations

This model is a **research prototype only** and is **not intended for clinical use**.

- **Class imbalance:** HAM10000 is dominated by NV (nevus, 66.9%). Accuracy alone is misleading — we report AUC-ROC, sensitivity and specificity.
- **Demographic bias:** The dataset consists predominantly of European skin tones (Rosendahl et al., 2018). Performance on darker skin tones is unvalidated and likely lower.
- **Clinical disclaimer:** Predictions should never replace dermatologist diagnosis. The model has no access to patient history, lesion evolution, or tactile examination.

Dataset license: [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)
