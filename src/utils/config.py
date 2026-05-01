from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR  = REPO_ROOT / 'data' / 'HAM10000'
IMG_DIR         = DATA_DIR / 'ISIC2018_Task3_Training_Input'
IMAGES_DIR      = IMG_DIR                                          # alias used by dataset.py
META_PATH       = DATA_DIR / 'ISIC2018_Task3_Training_GroundTruth' / 'ISIC2018_Task3_Training_GroundTruth.csv'
GROUND_TRUTH_CSV = META_PATH                                       # alias used by dataset.py
CKPT_DIR  = REPO_ROOT / 'checkpoints'
CKPT_DIR.mkdir(exist_ok=True)

# ── Label mapping ──────────────────────────────────────────────────────────
LABEL_COLS = ['MEL', 'NV', 'BCC', 'AKIEC', 'BKL', 'DF', 'VASC']
LABEL_MAP  = {
    'MEL'  : 'Melanoma',
    'NV'   : 'Melanocytic Nevi',
    'BCC'  : 'Basal Cell Carcinoma',
    'AKIEC': 'Actinic Keratosis',
    'BKL'  : 'Benign Keratosis',
    'DF'   : 'Dermatofibroma',
    'VASC' : 'Vascular Lesion',
}
NUM_CLASSES = len(LABEL_COLS)
# Sorted alphabetically — this is the class index order
CLASS_NAMES = sorted(LABEL_COLS)   # ['AKIEC','BCC','BKL','DF','MEL','NV','VASC']

# ── Training defaults ──────────────────────────────────────────────────────
IMG_SIZE   = 224
BATCH_SIZE = 32
NUM_EPOCHS = 30
LR         = 1e-4
WEIGHT_DECAY = 1e-5
VAL_SPLIT  = 0.2
SEED       = 42
NUM_WORKERS = 2
