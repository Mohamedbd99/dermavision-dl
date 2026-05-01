"""
conftest.py — shared pytest fixtures
=====================================

Fixtures available to ALL test files:
  - tmp_db          : fresh SQLite database (in-memory, per test)
  - client          : TestClient wired to the FastAPI app with tmp_db override
                      (model loading is MOCKED — tests run without GPU/checkpoint)
  - auth_client     : (client, token) with a pre-registered + logged-in user
  - sample_jpeg_bytes : minimal valid JPEG bytes for /predict tests
  - real_image_path : path to first HAM10000 image (skipped if dataset absent)

Design note — why we mock the lifespan
---------------------------------------
The production lifespan loads a 80 MB EfficientNet-B3 checkpoint onto the MPS
device, which takes ~8 s and should not run on every test. The `client` fixture
patches the lifespan with a lightweight stub that only creates DB tables and
sets placeholder values on `app.state`. Tests that genuinely need inference
(marked with `if not hasattr(c.app.state, 'model')`) are automatically skipped
in CI and can be run locally with the real server.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ── project imports ──────────────────────────────────────────────────────────
from sqlalchemy.pool import StaticPool

from src.api.database import Base, get_db
from src.api.main import app
from src.utils.config import REPO_ROOT


@pytest.fixture()
def tmp_db():
    """
    Create an isolated in-memory SQLite database for a single test.

    Uses StaticPool so every session shares the SAME single connection —
    required for SQLite in-memory because `sqlite://` would give each new
    connection its own empty database, causing "no such table" errors.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,   # ← force all sessions onto one connection
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def _get_db_override():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db_override
    yield engine
    Base.metadata.drop_all(engine)
    app.dependency_overrides.pop(get_db, None)


@asynccontextmanager
async def _mock_lifespan(app_instance):
    """
    Lightweight test lifespan: sets stub state only.
    Does NOT load the model or create DB tables
    (tmp_db fixture already creates tables in the test in-memory engine).
    """
    app_instance.state.model_name = "efficientnet_b3"
    app_instance.state.device = "cpu (mocked)"
    app_instance.state.checkpoint_name = "exp07-optuna-FINAL_best.pt (mocked)"
    yield


@pytest.fixture()
def client(tmp_db):
    """
    FastAPI TestClient backed by the in-memory test DB.
    Model loading is replaced by a lightweight mock lifespan.
    """
    with patch.object(app.router, "lifespan_context", _mock_lifespan):
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c


@pytest.fixture()
def registered_user(client):
    """Register a user and return (client, username, password)."""
    resp = client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@dermavision.ai",
            "password": "testpass99",
        },
    )
    assert resp.status_code == 201, resp.text
    return client, "testuser", "testpass99"


@pytest.fixture()
def auth_client(registered_user):
    """Return (client, bearer_token) with the test user already logged in."""
    c, username, password = registered_user
    resp = c.post("/auth/login", data={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return c, token


@pytest.fixture()
def sample_jpeg_bytes():
    """
    Minimal valid JPEG image (3×3 white pixels) encoded as bytes.
    Used to test /predict without needing the real dataset.
    """
    try:
        import cv2
        import numpy as np
        img = (np.ones((64, 64, 3), dtype="uint8") * 200)  # grey 64×64
        _, buf = cv2.imencode(".jpg", img)
        return buf.tobytes()
    except Exception:
        # fallback: a known-valid 1×1 white JPEG
        return (
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
            b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
            b"\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a"
            b"\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\x1e"
            b'\xc2\x00\x01\x01\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01'
            b'\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04'
            b'\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00'
            b'\xf5\x00\xff\xd9'
        )


@pytest.fixture()
def real_image_path():
    """
    Path to the first image in the HAM10000 training set.
    Tests that use this fixture are automatically skipped if the dataset
    is not present (dataset is gitignored — expected on dev machines only).
    """
    img_dir = REPO_ROOT / "data" / "HAM10000" / "ISIC2018_Task3_Training_Input"
    images = list(img_dir.glob("*.jpg"))
    if not images:
        pytest.skip("HAM10000 dataset not found — skipping real-image test")
    return images[0]
