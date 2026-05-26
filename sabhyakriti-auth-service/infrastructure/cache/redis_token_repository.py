from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import redis.asyncio as aioredis

from domain.entities.tokens import RefreshToken
from domain.repositories.i_token_repository import ITokenRepository

_TTL_SECONDS = 30 * 24 * 3600  # 30 days

# Lua script: revoke_all_for_user
# KEYS[1] = pattern prefix for SCAN  (not used directly — we pass it as arg)
# ARGV[1] = match pattern  e.g. "refresh:{user_id}:*"
_REVOKE_ALL_SCRIPT = """
local cursor = "0"
local pattern = ARGV[1]
repeat
    local result = redis.call("SCAN", cursor, "MATCH", pattern, "COUNT", 100)
    cursor = result[1]
    local keys = result[2]
    for _, k in ipairs(keys) do
        redis.call("DEL", k)
    end
until cursor == "0"
return 1
"""


class RedisTokenRepository(ITokenRepository):
    def __init__(self, redis: aioredis.Redis) -> None:
        self._r = redis

    # key helpers
    @staticmethod
    def _token_key(user_id: uuid.UUID, jti: uuid.UUID) -> str:
        return f"refresh:{user_id}:{jti}"

    @staticmethod
    def _hash_key(token_hash: str) -> str:
        return f"rth:{token_hash}"

    async def store(self, token: RefreshToken) -> None:
        token_key = self._token_key(token.user_id, token.token_id)
        hash_key = self._hash_key(token.token_hash)
        payload = json.dumps(
            {
                "token_hash": token.token_hash,
                "expires_at_ts": token.expires_at.timestamp(),
                "revoked": False,
                "user_id": str(token.user_id),
                "token_id": str(token.token_id),
            }
        )
        pipe = self._r.pipeline()
        pipe.set(token_key, payload, ex=_TTL_SECONDS)
        # reverse-lookup: hash → user_id:jti
        pipe.set(hash_key, f"{token.user_id}:{token.token_id}", ex=_TTL_SECONDS)
        await pipe.execute()

    async def find_by_hash(self, token_hash: str) -> RefreshToken | None:
        hash_key = self._hash_key(token_hash)
        ref: str | None = await self._r.get(hash_key)
        if not ref:
            return None
        user_id_str, jti_str = ref.split(":", 1)
        token_key = self._token_key(uuid.UUID(user_id_str), uuid.UUID(jti_str))
        raw: str | None = await self._r.get(token_key)
        if not raw:
            return None
        data = json.loads(raw)
        if data.get("revoked"):
            return None
        return RefreshToken(
            token_id=uuid.UUID(data["token_id"]),
            user_id=uuid.UUID(data["user_id"]),
            token_hash=data["token_hash"],
            expires_at=datetime.fromtimestamp(data["expires_at_ts"], tz=timezone.utc),
            created_at=datetime.fromtimestamp(data["expires_at_ts"] - _TTL_SECONDS, tz=timezone.utc),
            revoked_at=None,
        )

    async def revoke(self, token_id: uuid.UUID) -> None:
        # We need user_id; scan all keys matching refresh:*:{token_id}
        pattern = f"refresh:*:{token_id}"
        async for key in self._r.scan_iter(match=pattern, count=10):
            raw: str | None = await self._r.get(key)
            if raw:
                data = json.loads(raw)
                data["revoked"] = True
                ttl: int = await self._r.ttl(key)
                await self._r.set(key, json.dumps(data), ex=max(ttl, 1))
                # also remove reverse-lookup so it can't be found by hash
                await self._r.delete(self._hash_key(data["token_hash"]))
            break  # token_id is unique

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        pattern = f"refresh:{user_id}:*"
        # Collect and delete all token keys; also clean up reverse-lookup keys
        keys_to_delete: list[str] = []
        async for key in self._r.scan_iter(match=pattern, count=100):
            raw: str | None = await self._r.get(key)
            if raw:
                data = json.loads(raw)
                keys_to_delete.append(self._hash_key(data["token_hash"]))
            keys_to_delete.append(key)
        if keys_to_delete:
            await self._r.delete(*keys_to_delete)
