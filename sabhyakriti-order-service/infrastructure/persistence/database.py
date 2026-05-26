"""
Dual async SQLAlchemy engine setup.

- Primary engine  → write operations (INSERT, UPDATE, DELETE)
- Replica engine  → read operations  (SELECT)

Both use asyncpg with connection pooling.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from config import Settings


def _create_engine(url: str, echo: bool = False) -> AsyncEngine:
    # Ensure async driver is used
    url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return create_async_engine(
        url,
        echo=echo,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


def create_engines(settings: Settings) -> tuple[AsyncEngine, AsyncEngine]:
    """Return (primary_engine, replica_engine) pair."""
    echo = settings.app_env == "development"
    primary = _create_engine(settings.database_primary_url, echo=echo)
    replica = _create_engine(settings.database_replica_url, echo=echo)
    return primary, replica


def create_session_factories(
    primary: AsyncEngine,
    replica: AsyncEngine,
) -> tuple[async_sessionmaker[AsyncSession], async_sessionmaker[AsyncSession]]:
    """Return (write_session_factory, read_session_factory) pair."""
    write_factory = async_sessionmaker(
        bind=primary,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    read_factory = async_sessionmaker(
        bind=replica,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    return write_factory, read_factory


async def get_write_session(
    write_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """Dependency-injected write session with automatic rollback on error."""
    async with write_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_read_session(
    read_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """Dependency-injected read session (no commit needed)."""
    async with read_factory() as session:
        yield session
