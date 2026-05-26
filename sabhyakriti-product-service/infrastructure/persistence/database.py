"""Dual async SQLAlchemy engine setup (primary write + read replica)."""
from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_engines(
    primary_url: str,
    replica_url: str,
    *,
    pool_size: int = 10,
    max_overflow: int = 20,
    pool_timeout: int = 30,
    echo: bool = False,
) -> tuple[AsyncEngine, AsyncEngine]:
    """Create write (primary) and read (replica) async engines.

    Returns:
        Tuple of (primary_engine, replica_engine).
    """
    # Ensure async driver is used
    primary_url = primary_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    replica_url = replica_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    common_kwargs = {
        "pool_size": pool_size,
        "max_overflow": max_overflow,
        "pool_timeout": pool_timeout,
        "pool_pre_ping": True,
        "echo": echo,
    }
    primary_engine = create_async_engine(primary_url, **common_kwargs)
    replica_engine = create_async_engine(replica_url, **common_kwargs)
    return primary_engine, replica_engine


def create_session_factories(
    primary_engine: AsyncEngine,
    replica_engine: AsyncEngine,
) -> tuple[async_sessionmaker[AsyncSession], async_sessionmaker[AsyncSession]]:
    """Return (write_session_factory, read_session_factory)."""
    write_factory = async_sessionmaker(
        primary_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    read_factory = async_sessionmaker(
        replica_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    return write_factory, read_factory


async def get_write_session(
    write_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for a write session."""
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
    """FastAPI dependency for a read-only session."""
    async with read_factory() as session:
        yield session
