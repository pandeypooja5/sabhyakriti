"""Async SQLAlchemy engine and session factory.

A single engine instance is created at startup and shared across the process.
Each request gets its own ``AsyncSession`` via ``get_db`` in
``presentation/dependencies.py``.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared SQLAlchemy declarative base for all ORM models."""


# Module-level singletons — initialised in main.py lifespan
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_db(database_url: str) -> None:
    """Initialise the async engine and session factory.

    Must be called once during application startup before any DB calls.
    """
    global _engine, _session_factory  # noqa: PLW0603
    _engine = create_async_engine(
        database_url,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )
    _session_factory = async_sessionmaker(
        _engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )


async def close_db() -> None:
    """Dispose the engine connection pool during application shutdown."""
    global _engine  # noqa: PLW0603
    if _engine is not None:
        await _engine.dispose()
        _engine = None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the configured session factory.

    Raises:
        RuntimeError: If ``init_db`` has not been called.
    """
    if _session_factory is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")
    return _session_factory


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a single ``AsyncSession`` per request, with automatic rollback on error."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
