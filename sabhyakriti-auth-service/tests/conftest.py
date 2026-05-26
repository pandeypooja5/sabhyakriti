from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

import fakeredis.aioredis
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from domain.entities.user import User
from domain.value_objects import UserRole
from infrastructure.persistence.models import Base
from main import create_app


@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.DefaultEventLoopPolicy()


@pytest_asyncio.fixture
async def fake_redis():
    r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield r
    await r.aclose()


@pytest_asyncio.fixture
async def db_session(postgresql):
    url = f"postgresql+asyncpg://{postgresql.info.user}:{postgresql.info.password}@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


def make_user(**kwargs: Any) -> User:
    from datetime import datetime, timezone
    now = datetime.now(tz=timezone.utc)
    defaults = dict(
        user_id=uuid4(), email="test@example.com", full_name="Test User",
        role=UserRole.CUSTOMER, is_email_verified=True, is_phone_verified=False,
        is_active=True, failed_login_attempts=0, mfa_enabled=False,
        created_at=now, updated_at=now,
    )
    defaults.update(kwargs)
    return User(**defaults)


@pytest.fixture
def mock_hibp():
    m = AsyncMock()
    m.is_password_breached.return_value = False
    return m


@pytest.fixture
def mock_sms():
    m = AsyncMock()
    m.send_otp.return_value = None
    return m


@pytest.fixture
def mock_email():
    m = AsyncMock()
    m.send_verification_email.return_value = None
    m.send_password_reset_email.return_value = None
    return m
