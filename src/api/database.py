"""
database.py — SQLite persistence layer
=======================================
Uses SQLAlchemy 2.x with a simple SQLite file stored at:
    <repo_root>/dermavision.db

Tables
------
users
    id          INTEGER  PK autoincrement
    username    TEXT     unique, not-null
    email       TEXT     unique, not-null
    hashed_pwd  TEXT     not-null
    is_active   BOOLEAN  default True
    created_at  DATETIME default now()

predictions (audit log — every /predict call is stored)
    id          INTEGER  PK autoincrement
    user_id     INTEGER  FK → users.id
    filename    TEXT
    predicted_class TEXT
    confidence  FLOAT
    all_scores  TEXT     (JSON string of {class: prob})
    created_at  DATETIME default now()

Usage
-----
    from src.api.database import get_db, User, Prediction
    # FastAPI: Depends(get_db)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text, create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

from src.utils.config import REPO_ROOT

# ── Engine ─────────────────────────────────────────────────────────────────
DB_PATH = REPO_ROOT / "dermavision.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # needed for SQLite + FastAPI
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# ── ORM Base ────────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Models ──────────────────────────────────────────────────────────────────
class User(Base):
    """Registered user account."""

    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username: str = Column(String(50), unique=True, nullable=False, index=True)
    email: str = Column(String(120), unique=True, nullable=False, index=True)
    hashed_pwd: str = Column(String(256), nullable=False)
    is_active: bool = Column(Boolean, default=True)
    created_at: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    predictions = relationship(
        "Prediction", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"


class Prediction(Base):
    """Audit log entry for each /predict call."""

    __tablename__ = "predictions"

    id: int = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename: str = Column(String(255), nullable=True)
    image_path: str = Column(String(512), nullable=True)   # relative path under uploads/
    predicted_class: str = Column(String(20), nullable=False)
    confidence: float = Column(Float, nullable=False)
    all_scores: str = Column(Text, nullable=False)   # JSON {"AKIEC": 0.01, ...}
    created_at: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="predictions")

    # ── helpers ──────────────────────────────────────────────────────────
    def scores_dict(self) -> dict[str, float]:
        """Deserialise the JSON scores back to a dict."""
        return json.loads(self.all_scores)

    def __repr__(self) -> str:
        return (
            f"<Prediction id={self.id} class={self.predicted_class!r} "
            f"conf={self.confidence:.3f}>"
        )


# ── DB init ─────────────────────────────────────────────────────────────────
def init_db() -> None:
    """Create all tables if they don't exist yet (called at app startup)."""
    Base.metadata.create_all(bind=engine)


# ── FastAPI dependency ───────────────────────────────────────────────────────
def get_db():
    """
    Yield a SQLAlchemy session, guarantee it is closed after the request.

    Usage in route:
        def some_route(db: Session = Depends(get_db)): ...
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
