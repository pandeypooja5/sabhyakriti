"""Async SQLAlchemy engine and session factory."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Engine and factory singletons — initialised in main.py lifespan
_engine = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_db(database_url: str) -> None:
    """Create the async engine and session factory from the given URL."""
    global _engine, _async_session_factory

    _engine = create_async_engine(
        database_url,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    _async_session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the session factory, raising if not yet initialised."""
    if _async_session_factory is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")
    return _async_session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yield a scoped database session."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def close_db() -> None:
    """Dispose of the async engine during application shutdown."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
