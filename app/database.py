"""Database configuration and session management for Book Catalog.

Supports SQLite for local development and PostgreSQL for containerized deployments.
Configured via DATABASE_URL environment variable.
"""

import os
from collections.abc import Generator
from typing import Final

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DEFAULT_SQLITE_URL: Final[str] = "sqlite:///./book_catalog.db"
DATABASE_URL: Final[str] = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)

is_sqlite = DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy database models."""

    pass


def get_db() -> Generator[Session]:
    """Provide a transactional database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
