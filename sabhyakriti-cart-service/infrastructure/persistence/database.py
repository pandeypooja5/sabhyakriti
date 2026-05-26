"""Async SQLAlchemy engine and session factory.

Single engine instance is created at startup and reused across requests.
"""

from __future__ import annotations

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

# ---------------------------------------------------------------------------
# ORM base
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


# ---------------------------------------------------------------------------
# Module-level singletons (populated at startup via init_db)
# ---------------------------------------------------------------------------

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_db(database_url: str | None = None) -> None:
    """Initialise the async engine and session factory.

    Must be called once at application startup (inside lifespan).

    Args:
        database_url: override for testing; defaults to DATABASE_URL env var
    """
    global _engine, _session_factory

    url = database_url or os.environ["DATABASE_URL"]

    _engine = create_async_engine(
        url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=os.getenv("LOG_LEVEL", "INFO").upper() == "DEBUG",
    )

    _session_factory = async_sessionmaker(
        _engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )


def get_engine() -> AsyncEngine:
    if _engine is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    if _session_factory is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")
    return _session_factory


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session per request."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def close_db() -> None:
    """Dispose the engine pool (called at shutdown)."""
    if _engine is not None:
        await _engine.dispose()
