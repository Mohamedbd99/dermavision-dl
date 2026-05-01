"""
auth.py — Authentication utilities
====================================
Implements:
  • Password hashing / verification  (bcrypt via passlib)
  • JWT access-token creation        (HS256 via python-jose)
  • FastAPI dependency get_current_user()

Token format
------------
    Header  : {"alg": "HS256", "typ": "JWT"}
    Payload : {"sub": "<username>", "exp": <unix ts>}

Environment variables (override defaults for production)
---------------------------------------------------------
    SECRET_KEY      - 256-bit random hex string  (default: dev placeholder)
    ACCESS_TOKEN_EXPIRE_MINUTES - token lifetime (default: 60 minutes)

Usage in routes
---------------
    from src.api.auth import get_current_user
    from src.api.database import User

    @router.get("/protected")
    def protected(current_user: User = Depends(get_current_user)):
        ...
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from src.api.database import User, get_db

# ── Configuration ───────────────────────────────────────────────────────────
# NOTE: In production set SECRET_KEY via environment variable — never hardcode!
SECRET_KEY: str = os.getenv(
    "SECRET_KEY",
    "CHANGE_ME_in_production_use_openssl_rand_hex_32",
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)

# OAuth2 scheme — points to the /auth/login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ── Password helpers ────────────────────────────────────────────────────────
def hash_password(plain: str) -> str:
    """Return the bcrypt hash of *plain*."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches the stored *hashed* password."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ── JWT helpers ─────────────────────────────────────────────────────────────
def create_access_token(subject: str) -> str:
    """
    Create a signed JWT with *subject* as the ``sub`` claim.

    Args:
        subject: username (unique identifier stored in the token)

    Returns:
        Encoded JWT string, valid for ACCESS_TOKEN_EXPIRE_MINUTES minutes.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _decode_token(token: str) -> str:
    """
    Decode a JWT and return the ``sub`` claim (username).

    Raises HTTPException 401 if the token is invalid or expired.
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exc
        return username
    except JWTError:
        raise credentials_exc


# ── FastAPI dependency ───────────────────────────────────────────────────────
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency — resolve Bearer token → User ORM object.

    Raises HTTP 401 if the token is missing, expired, or the user no
    longer exists in the database.
    Raises HTTP 403 if the account is inactive.
    """
    username = _decode_token(token)
    user: Optional[User] = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive account",
        )
    return user
