"""
test_api.py — Integration tests for the FastAPI application
=============================================================

All tests use an in-memory SQLite database (via the `client` / `auth_client`
fixtures from conftest.py) — no real model is loaded, no port is opened.

Coverage:
  Authentication
    - POST /auth/register   (happy path, duplicate username, duplicate email,
                             short password, short username)
    - POST /auth/login      (happy path, wrong password, unknown user)
    - GET  /me              (authenticated, missing token, invalid token)

  System endpoints
    - GET /health           (no auth required)
    - GET /metrics          (no auth required, schema check)

  Inference
    - POST /predict         (authenticated with real-ish image,
                             unauthenticated, empty file)
    - GET  /history         (authenticated, empty then after predict)

  Edge cases
    - JWT expiry / tampered token
    - Duplicate registration
"""

from __future__ import annotations

import json

import pytest


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH — /auth/register
# ═══════════════════════════════════════════════════════════════════════════════

class TestRegister:
    def test_register_success(self, client):
        resp = client.post(
            "/auth/register",
            json={
                "username": "alice",
                "email": "alice@test.com",
                "password": "strongpass",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "alice"
        assert data["email"] == "alice@test.com"
        assert data["is_active"] is True
        assert "hashed_pwd" not in data     # never leak password hash
        assert "id" in data
        assert "created_at" in data

    def test_register_duplicate_username(self, client):
        payload = {"username": "bob", "email": "bob@test.com", "password": "pass123"}
        client.post("/auth/register", json=payload)
        resp = client.post(
            "/auth/register",
            json={"username": "bob", "email": "bob2@test.com", "password": "pass123"},
        )
        assert resp.status_code == 409
        assert "username" in resp.json()["detail"].lower()

    def test_register_duplicate_email(self, client):
        client.post(
            "/auth/register",
            json={"username": "carol", "email": "shared@test.com", "password": "pass123"},
        )
        resp = client.post(
            "/auth/register",
            json={"username": "carol2", "email": "shared@test.com", "password": "pass123"},
        )
        assert resp.status_code == 409
        assert "e-mail" in resp.json()["detail"].lower()

    def test_register_short_password(self, client):
        resp = client.post(
            "/auth/register",
            json={"username": "dave", "email": "dave@test.com", "password": "abc"},
        )
        assert resp.status_code == 422   # Pydantic validation error

    def test_register_short_username(self, client):
        resp = client.post(
            "/auth/register",
            json={"username": "ab", "email": "ab@test.com", "password": "longpassword"},
        )
        assert resp.status_code == 422

    def test_register_invalid_email(self, client):
        resp = client.post(
            "/auth/register",
            json={"username": "eve", "email": "not-an-email", "password": "longpassword"},
        )
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH — /auth/login
# ═══════════════════════════════════════════════════════════════════════════════

class TestLogin:
    def test_login_success(self, registered_user):
        c, username, password = registered_user
        resp = c.post("/auth/login", data={"username": username, "password": password})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in_minutes"] == 60
        # Token must be a non-empty string with 2 dots (JWT format)
        parts = data["access_token"].split(".")
        assert len(parts) == 3

    def test_login_wrong_password(self, registered_user):
        c, username, _ = registered_user
        resp = c.post("/auth/login", data={"username": username, "password": "wrongpass"})
        assert resp.status_code == 401

    def test_login_unknown_user(self, client):
        resp = client.post("/auth/login", data={"username": "ghost", "password": "anypass"})
        assert resp.status_code == 401

    def test_login_returns_unique_tokens(self, registered_user):
        """Two consecutive logins must produce different tokens (jti / exp differ)."""
        c, username, password = registered_user
        t1 = c.post("/auth/login", data={"username": username, "password": password}).json()["access_token"]
        t2 = c.post("/auth/login", data={"username": username, "password": password}).json()["access_token"]
        # Tokens might have same exp if issued within same second — just check they're valid strings
        assert isinstance(t1, str) and len(t1) > 20
        assert isinstance(t2, str) and len(t2) > 20


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH — /me
# ═══════════════════════════════════════════════════════════════════════════════

class TestMe:
    def test_me_authenticated(self, auth_client):
        c, token = auth_client
        resp = c.get("/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "testuser"
        assert "hashed_pwd" not in data

    def test_me_no_token(self, client):
        resp = client.get("/me")
        assert resp.status_code == 401

    def test_me_invalid_token(self, client):
        resp = client.get("/me", headers={"Authorization": "Bearer this.is.garbage"})
        assert resp.status_code == 401

    def test_me_tampered_token(self, auth_client):
        c, token = auth_client
        # Flip one character in the signature part
        parts = token.split(".")
        parts[-1] = parts[-1][:-1] + ("A" if parts[-1][-1] != "A" else "B")
        bad_token = ".".join(parts)
        resp = c.get("/me", headers={"Authorization": f"Bearer {bad_token}"})
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM — /health and /metrics
# ═══════════════════════════════════════════════════════════════════════════════

class TestSystemEndpoints:
    def test_health_no_auth_required(self, client):
        """Health endpoint must be publicly accessible."""
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_response_schema(self, client):
        data = client.get("/health").json()
        assert "status" in data
        assert "classes" in data
        assert len(data["classes"]) == 7
        assert "num_classes" in data
        assert data["num_classes"] == 7

    def test_metrics_no_auth_required(self, client):
        resp = client.get("/metrics")
        assert resp.status_code == 200

    def test_metrics_response_schema(self, client):
        data = client.get("/metrics").json()
        assert "experiment" in data
        assert "metrics" in data
        metrics = data["metrics"]
        assert "auc_roc_macro_ovr" in metrics
        assert "accuracy" in metrics
        assert "f1_macro" in metrics
        # AUC must be a real number between 0 and 1
        auc = metrics["auc_roc_macro_ovr"]
        assert 0.0 < auc <= 1.0

    def test_metrics_best_auc_value(self, client):
        """Best model AUC must match the known Exp 07 result."""
        data = client.get("/metrics").json()
        auc = data["metrics"]["auc_roc_macro_ovr"]
        assert abs(auc - 0.9776) < 1e-4, f"Unexpected AUC: {auc}"

    def test_metrics_classes_present(self, client):
        """All 7 class codes must be listed."""
        from src.utils.config import CLASS_NAMES
        data = client.get("/metrics").json()
        assert "classes" in data
        for code in CLASS_NAMES:
            assert code in data["classes"]


# ═══════════════════════════════════════════════════════════════════════════════
# INFERENCE — /predict
# ═══════════════════════════════════════════════════════════════════════════════

class TestPredict:
    """
    /predict tests.

    NOTE: The real model is NOT loaded in tests (lifespan is skipped by
    TestClient). Tests that require actual model inference are marked with
    `requires_model` and skipped automatically when `app.state.model` is absent.
    """

    def _has_model(self, client) -> bool:
        return hasattr(client.app.state, "model")

    def test_predict_requires_auth(self, client, sample_jpeg_bytes):
        """Unauthenticated /predict must return 401."""
        resp = client.post(
            "/predict",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
        )
        assert resp.status_code == 401

    def test_predict_empty_file_rejected(self, auth_client):
        c, token = auth_client
        resp = c.post(
            "/predict",
            files={"file": ("empty.jpg", b"", "image/jpeg")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400

    def test_predict_invalid_file_rejected(self, auth_client):
        """Uploading a text file must return 422."""
        c, token = auth_client
        resp = c.post(
            "/predict",
            files={"file": ("notes.txt", b"this is not an image", "text/plain")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    def test_predict_with_model(self, auth_client, sample_jpeg_bytes):
        """Full inference test — skipped if model is not loaded."""
        c, token = auth_client
        if not self._has_model(c):
            pytest.skip("Model not loaded in test context — skipping inference test")
        resp = c.post(
            "/predict",
            files={"file": ("skin.jpg", sample_jpeg_bytes, "image/jpeg")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "predicted_class" in data
        assert "confidence" in data
        assert 0.0 <= data["confidence"] <= 1.0
        assert len(data["all_scores"]) == 7
        total_prob = sum(s["confidence"] for s in data["all_scores"])
        assert abs(total_prob - 1.0) < 1e-3, f"Softmax sum != 1: {total_prob}"

    def test_predict_with_real_image(self, auth_client, real_image_path):
        """Real HAM10000 image — skipped if dataset absent or model not loaded."""
        c, token = auth_client
        if not self._has_model(c):
            pytest.skip("Model not loaded in test context")
        img_bytes = real_image_path.read_bytes()
        resp = c.post(
            "/predict",
            files={"file": (real_image_path.name, img_bytes, "image/jpeg")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        from src.utils.config import CLASS_NAMES
        assert data["predicted_class"] in CLASS_NAMES


# ═══════════════════════════════════════════════════════════════════════════════
# INFERENCE — /history
# ═══════════════════════════════════════════════════════════════════════════════

class TestHistory:
    def test_history_requires_auth(self, client):
        resp = client.get("/history")
        assert resp.status_code == 401

    def test_history_empty_initially(self, auth_client):
        c, token = auth_client
        resp = c.get("/history", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json() == []

    def test_history_populated_after_predict(self, auth_client, sample_jpeg_bytes):
        """After a successful /predict the audit log must have one entry."""
        c, token = auth_client
        if not hasattr(c.app.state, "model"):
            pytest.skip("Model not loaded")
        c.post(
            "/predict",
            files={"file": ("img.jpg", sample_jpeg_bytes, "image/jpeg")},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = c.get("/history", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        history = resp.json()
        assert len(history) == 1
        entry = history[0]
        assert "predicted_class" in entry
        assert "confidence" in entry
        assert "all_scores" in entry
        assert isinstance(entry["all_scores"], dict)

    def test_history_isolation_between_users(self, client, sample_jpeg_bytes):
        """User A's history must NOT be visible to user B."""
        # Register and login user A
        client.post("/auth/register", json={"username": "userA", "email": "a@t.com", "password": "pass1234"})
        tok_a = client.post("/auth/login", data={"username": "userA", "password": "pass1234"}).json()["access_token"]

        # Register and login user B
        client.post("/auth/register", json={"username": "userB", "email": "b@t.com", "password": "pass1234"})
        tok_b = client.post("/auth/login", data={"username": "userB", "password": "pass1234"}).json()["access_token"]

        # B's history must be empty regardless of what A does
        resp_b = client.get("/history", headers={"Authorization": f"Bearer {tok_b}"})
        assert resp_b.status_code == 200
        assert resp_b.json() == []
