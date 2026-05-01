"""
main.py — FastAPI application factory
=======================================

Start the server
----------------
    # Development (auto-reload)
    uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

    # Or use the convenience script at the repo root:
    python run_api.py

Interactive docs
----------------
    Swagger UI  →  http://localhost:8000/docs
    ReDoc       →  http://localhost:8000/redoc
    OpenAPI JSON →  http://localhost:8000/openapi.json

Architecture
------------
    main.py           ← you are here (app factory, lifespan, middleware)
    ├── database.py   ← SQLAlchemy models + get_db dependency
    ├── auth.py       ← bcrypt + JWT helpers + get_current_user dependency
    └── endpoints.py  ← all route handlers (auth, predict, health, metrics …)

Model loading
-------------
The EfficientNet-B3 checkpoint (Exp 07 Optuna FINAL — AUC 0.9776) is loaded
ONCE at startup via the lifespan context manager and stored on `app.state`.
All /predict calls reuse the same in-memory model — no per-request reload.

    app.state.model          DermaVisionModel (eval mode)
    app.state.device         torch.device  (mps / cuda / cpu)
    app.state.transforms     Albumentations val pipeline
    app.state.model_name     "efficientnet_b3"
    app.state.checkpoint_name filename of the .pt file
"""

from __future__ import annotations

from contextlib import asynccontextmanager

import torch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.database import init_db
from src.api.endpoints import router
from src.data.preprocessing import get_val_transforms
from src.models.architecture import DermaVisionModel
from src.utils.config import CKPT_DIR, CLASS_NAMES

# ── Constants ────────────────────────────────────────────────────────────────
CHECKPOINT_FILE = "exp07-optuna-FINAL_best.pt"
BACKBONE = "efficientnet_b3"
DROPOUT = 0.229          # Optuna best trial value


# ── Lifespan (startup / shutdown) ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context.

    Startup
    -------
    1. Initialise SQLite tables (idempotent — safe to call every time).
    2. Detect best available compute device (MPS → CUDA → CPU).
    3. Load DermaVisionModel from checkpoint and store on app.state.
    4. Store albumentations val transforms on app.state.

    Shutdown
    --------
    (nothing required — Python GC handles cleanup)
    """
    # ── 1. DB tables ─────────────────────────────────────────────────────
    init_db()

    # ── 2. Device ─────────────────────────────────────────────────────────
    if torch.backends.mps.is_available():
        device = torch.device("mps")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")

    # ── 3. Model ──────────────────────────────────────────────────────────
    ckpt_path = CKPT_DIR / CHECKPOINT_FILE
    if not ckpt_path.exists():
        raise FileNotFoundError(
            f"Checkpoint not found: {ckpt_path}\n"
            "Run `python -m src.models.training --exp_name exp07-optuna-FINAL` "
            "or download the .pt file into the checkpoints/ directory."
        )

    model = DermaVisionModel(
        backbone=BACKBONE,
        num_classes=len(CLASS_NAMES),
        pretrained=False,   # weights come from checkpoint
        dropout=DROPOUT,
    )
    state_dict = torch.load(ckpt_path, map_location=device)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    # ── 4. Store on app.state ─────────────────────────────────────────────
    app.state.model = model
    app.state.device = device
    app.state.transforms = get_val_transforms()
    app.state.model_name = BACKBONE
    app.state.checkpoint_name = CHECKPOINT_FILE

    print(f"[DermaVision API] Model loaded — device={device}  checkpoint={CHECKPOINT_FILE}")

    yield   # ← server is running here

    # Shutdown (nothing to do)
    print("[DermaVision API] Shutting down.")


# ── App factory ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="DermaVision API",
    description="""
## Skin Lesion Classification API

Classify dermoscopy images into **7 skin lesion categories** using a deep
learning model (EfficientNet-B3, AUC-ROC = 0.9776 on HAM10000 validation set).

---

### Quick start

1. **Register** an account → `POST /auth/register`
2. **Login** to get a JWT token → `POST /auth/login`
3. **Authorise** — click the 🔒 button in Swagger UI and enter `Bearer <token>`
4. **Upload** a dermoscopy image → `POST /predict`

---

### Classes

| Code | Full name | Prevalence (HAM10000) |
|------|-----------|-----------------------|
| AKIEC | Actinic Keratosis | 3.3 % |
| BCC | Basal Cell Carcinoma | 5.1 % |
| BKL | Benign Keratosis | 11.0 % |
| DF | Dermatofibroma | 1.1 % |
| MEL | Melanoma | 11.1 % |
| NV | Melanocytic Nevi | 66.9 % |
| VASC | Vascular Lesion | 1.4 % |

---

> ⚠️ **Disclaimer** — This API is for **research and educational purposes only**.
> It is NOT a certified medical device.
> Do NOT use it for clinical diagnosis or treatment decisions.
    """,
    version="1.0.0",
    contact={
        "name": "DermaVision Team",
        "url": "https://github.com/Mohamedbd99/dermavision-dl",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
    # Swagger UI served at /docs — ReDoc at /redoc
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
# Allow all origins in development.  Restrict to your frontend domain in prod.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount routes ─────────────────────────────────────────────────────────────
app.include_router(router)

# Serve uploaded images at /uploads/<filename>
from pathlib import Path
from fastapi.staticfiles import StaticFiles

_uploads_dir = Path("uploads")
_uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_uploads_dir)), name="uploads")
