from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import fakeredis.aioredis
import pytest
import pytest_asyncio

from domain.entities.tokens import RefreshToken
from infrastructure.cache.redis_token_repository import RedisTokenRepository

NOW = datetime.now(tz=timezone.utc)


@pytest_asyncio.fixture
async def redis():
    r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield r
    await r.aclose()


@pytest_asyncio.fixture
async def repo(redis):
    return RedisTokenRepository(redis)


@pytest.mark.asyncio
async def test_store_and_find(repo: RedisTokenRepository) -> None:
    token = RefreshToken(
        token_id=uuid4(), user_id=uuid4(), token_hash="hash123",
        expires_at=NOW + timedelta(days=30), created_at=NOW,
    )
    await repo.store(token)
    found = await repo.find_by_hash("hash123")
    assert found is not None
    assert found.token_id == token.token_id


@pytest.mark.asyncio
async def test_revoke(repo: RedisTokenRepository) -> None:
    token = RefreshToken(
        token_id=(tid := uuid4()), user_id=uuid4(), token_hash="hash_revoke",
        expires_at=NOW + timedelta(days=30), created_at=NOW,
    )
    await repo.store(token)
    await repo.revoke(tid)
    found = await repo.find_by_hash("hash_revoke")
    assert found is None or not found.is_valid(NOW)


@pytest.mark.asyncio
async def test_revoke_all_for_user(repo: RedisTokenRepository) -> None:
    user_id = uuid4()
    for _ in range(3):
        t = RefreshToken(
            token_id=uuid4(), user_id=user_id,
            token_hash=f"hash_{uuid4().hex}",
            expires_at=NOW + timedelta(days=30), created_at=NOW,
        )
        await repo.store(t)
    await repo.revoke_all_for_user(user_id)
    # All tokens for this user should be gone
    import redis.asyncio as aioredis
    keys = [k async for k in repo._redis.scan_iter(f"refresh:{user_id}:*")]
    assert len(keys) == 0
