"""
endpoints.py — All API route handlers
=======================================

Router structure
----------------
    /auth
        POST  /register   — create a new user account
        POST  /login      — exchange credentials for a JWT token

    /health               — liveness probe (no auth required)

    /metrics              — model performance summary (no auth required)

    /predict              — classify a skin lesion image  (🔒 JWT required)

    /history              — list the calling user's past predictions (🔒 JWT)

Notes
-----
- The model is NOT loaded here. It is loaded once at app startup (main.py)
  and stored in `app.state.model` / `app.state.device` / `app.state.transforms`.
  Endpoints access it via the `Request` object.
- Images are decoded with OpenCV (BGR→RGB) to match training preprocessing.
- Prediction scores are stored in the `predictions` table for every call.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from io import BytesIO
from typing import Dict, List, Optional

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.orm import Session

from src.api.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from src.api.database import Prediction, User, get_db
from src.utils.config import CLASS_NAMES, LABEL_MAP

router = APIRouter()

# ── Pydantic schemas ────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    """Body for POST /auth/register."""
    username: str
    email: EmailStr
    password: str

    @field_validator("username")
    @classmethod
    def username_min_length(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError("username must be at least 3 characters")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("password must be at least 6 characters")
        return v


class UserOut(BaseModel):
    """Safe user representation (no password field)."""
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class ClassScore(BaseModel):
    """Per-class confidence score."""
    code: str           # e.g. "MEL"
    full_name: str      # e.g. "Melanoma"
    confidence: float   # 0.0 – 1.0


class PredictionOut(BaseModel):
    """Full prediction response returned by /predict."""
    predicted_class: str
    predicted_class_full: str
    confidence: float
    all_scores: List[ClassScore]
    filename: Optional[str]
    logged_at: datetime


class PredictionHistoryItem(BaseModel):
    """One row from the predictions audit log."""
    id: int
    filename: Optional[str]
    predicted_class: str
    confidence: float
    all_scores: Dict[str, float]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── /auth ───────────────────────────────────────────────────────────────────

@router.post(
    "/auth/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    tags=["Authentication"],
)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """
    Create a new user account.

    - **username**: 3–50 characters, must be unique
    - **email**: valid e-mail address, must be unique
    - **password**: minimum 6 characters (stored as bcrypt hash — never plain text)
    """
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail already registered",
        )
    user = User(
        username=body.username,
        email=body.email,
        hashed_pwd=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post(
    "/auth/login",
    response_model=TokenOut,
    summary="Login and obtain a JWT token",
    tags=["Authentication"],
)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Authenticate with **username** + **password** (OAuth2 form body).

    Returns a Bearer JWT token valid for 60 minutes.  
    Pass it in the `Authorization: Bearer <token>` header to access protected endpoints.
    """
    user: User | None = (
        db.query(User).filter(User.username == form.username).first()
    )
    if user is None or not verify_password(form.password, user.hashed_pwd):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )
    token = create_access_token(subject=user.username)
    return TokenOut(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=60,
    )


# ── /health ──────────────────────────────────────────────────────────────────

@router.get(
    "/health",
    summary="Health check",
    tags=["System"],
)
def health(request: Request):
    """
    Liveness probe.  
    Returns the API version, model name and the compute device in use.
    """
    state = request.app.state
    return {
        "status": "ok",
        "model": getattr(state, "model_name", "unknown"),
        "device": str(getattr(state, "device", "unknown")),
        "checkpoint": getattr(state, "checkpoint_name", "unknown"),
        "classes": CLASS_NAMES,
        "num_classes": len(CLASS_NAMES),
    }


# ── /metrics ─────────────────────────────────────────────────────────────────

@router.get(
    "/metrics",
    summary="Model performance summary (best experiment)",
    tags=["System"],
)
def metrics():
    """
    Returns the performance metrics of the deployed model (Exp 07 — Optuna FINAL).

    Metrics were computed on the **held-out validation set** (2 003 images,
    stratified 80/20 split from HAM10000).  
    No data leakage — the validation split was fixed with `SEED=42` before
    any training began.
    """
    return {
        "experiment": "exp07-optuna-FINAL",
        "backbone": "efficientnet_b3",
        "dataset": "ISIC 2018 Task 3 — HAM10000",
        "val_split": "20 % stratified (2 003 images)",
        "epochs": 20,
        "hyperparameters": {
            "learning_rate": 2.36e-4,
            "weight_decay": 8.2e-6,
            "dropout": 0.229,
            "scheduler": "cosine",
            "class_weights": True,
            "mixup": False,
            "advanced_aug": True,
        },
        "metrics": {
            "auc_roc_macro_ovr": 0.9776,
            "accuracy": 0.8542,
            "f1_macro": 0.7962,
            "sensitivity_macro": 0.8284,
            "specificity_macro": 0.9697,
        },
        "classes": {code: LABEL_MAP[code] for code in CLASS_NAMES},
        "note": (
            "AUC-ROC is the primary metric. "
            "Class imbalance is handled with inverse-frequency weights during training."
        ),
    }


# ── /predict ─────────────────────────────────────────────────────────────────

@router.post(
    "/predict",
    response_model=PredictionOut,
    summary="Classify a skin lesion image",
    tags=["Inference"],
)
def predict(
    request: Request,
    file: UploadFile = File(..., description="Dermatoscopy image (JPEG/PNG)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a dermatoscopy image and receive a classification.

    **Authentication required** — pass `Authorization: Bearer <token>` header.

    ### What happens under the hood
    1. Image bytes are decoded with OpenCV (BGR→RGB), matching training preprocessing.
    2. Albumentations val pipeline: resize to 224×224, ImageNet normalisation.
    3. EfficientNet-B3 forward pass (Exp 07 checkpoint, AUC=0.9776).
    4. Softmax over 7 classes → top-1 prediction returned, all scores logged.

    ### Classes
    | Code | Full name |
    |------|-----------|
    | AKIEC | Actinic Keratosis |
    | BCC | Basal Cell Carcinoma |
    | BKL | Benign Keratosis |
    | DF | Dermatofibroma |
    | MEL | Melanoma |
    | NV | Melanocytic Nevi |
    | VASC | Vascular Lesion |

    > ⚠️ This tool is for **research / educational purposes only**.
    > It is NOT a medical device and must NOT be used for clinical diagnosis.
    """
    # ── Read & decode image ──────────────────────────────────────────────
    image_bytes = file.file.read()
    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    np_arr = np.frombuffer(image_bytes, np.uint8)
    bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if bgr is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not decode image — make sure it is a valid JPEG or PNG",
        )
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    # ── Apply validation transforms ──────────────────────────────────────
    state = request.app.state
    augmented = state.transforms(image=rgb)
    tensor: torch.Tensor = augmented["image"].unsqueeze(0)  # (1, 3, 224, 224)

    # ── Inference ────────────────────────────────────────────────────────
    device: torch.device = state.device
    tensor = tensor.to(device)

    with torch.no_grad():
        logits = state.model(tensor)              # (1, 7)
        probs = F.softmax(logits, dim=-1)[0]      # (7,)

    probs_cpu = probs.cpu().numpy().tolist()

    # ── Build result ─────────────────────────────────────────────────────
    scores = {cls: float(prob) for cls, prob in zip(CLASS_NAMES, probs_cpu)}
    top_class = max(scores, key=scores.__getitem__)
    top_conf = scores[top_class]

    all_scores_out = [
        ClassScore(
            code=cls,
            full_name=LABEL_MAP.get(cls, cls),
            confidence=round(prob, 6),
        )
        for cls, prob in sorted(scores.items(), key=lambda x: x[1], reverse=True)
    ]

    # ── Persist to DB ─────────────────────────────────────────────────────
    pred_row = Prediction(
        user_id=current_user.id,
        filename=file.filename,
        predicted_class=top_class,
        confidence=top_conf,
        all_scores=json.dumps(scores),
    )
    db.add(pred_row)
    db.commit()
    db.refresh(pred_row)

    return PredictionOut(
        predicted_class=top_class,
        predicted_class_full=LABEL_MAP.get(top_class, top_class),
        confidence=round(top_conf, 6),
        all_scores=all_scores_out,
        filename=file.filename,
        logged_at=pred_row.created_at,
    )


# ── /history ─────────────────────────────────────────────────────────────────

@router.get(
    "/history",
    response_model=List[PredictionHistoryItem],
    summary="Your prediction history",
    tags=["Inference"],
)
def history(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return the last *limit* predictions made by the authenticated user.

    Results are sorted newest-first.  
    Default limit is 50; max recommended is 200.
    """
    rows = (
        db.query(Prediction)
        .filter(Prediction.user_id == current_user.id)
        .order_by(Prediction.created_at.desc())
        .limit(limit)
        .all()
    )
    # Deserialise all_scores JSON for each row
    out = []
    for row in rows:
        out.append(
            PredictionHistoryItem(
                id=row.id,
                filename=row.filename,
                predicted_class=row.predicted_class,
                confidence=row.confidence,
                all_scores=row.scores_dict(),
                created_at=row.created_at,
            )
        )
    return out


# ── /me ──────────────────────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=UserOut,
    summary="Current authenticated user info",
    tags=["Authentication"],
)
def me(current_user: User = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    return current_user
