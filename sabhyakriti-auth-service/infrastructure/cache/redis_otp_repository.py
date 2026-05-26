from __future__ import annotations

import json
from datetime import datetime, timezone

import redis.asyncio as aioredis

from domain.entities.otp_record import OTPRecord
from domain.repositories.i_otp_repository import IOTPRepository

_OTP_TTL_SECONDS = 10 * 60  # 10 minutes


class RedisOTPRepository(IOTPRepository):
    def __init__(self, redis: aioredis.Redis) -> None:
        self._r = redis

    @staticmethod
    def _key(phone_number: str) -> str:
        return f"otp:{phone_number}"

    async def upsert(self, record: OTPRecord) -> None:
        key = self._key(record.phone_number)
        payload = json.dumps(
            {
                "otp_hash": record.otp_hash,
                "attempt_count": record.attempt_count,
                "last_sent_at_ts": record.last_sent_at.timestamp(),
                "expires_at_ts": record.expires_at.timestamp(),
                "used_at_ts": record.used_at.timestamp() if record.used_at else None,
            }
        )
        await self._r.set(key, payload, ex=_OTP_TTL_SECONDS)

    async def find_by_phone(self, phone_number: str) -> OTPRecord | None:
        key = self._key(phone_number)
        raw: str | None = await self._r.get(key)
        if not raw:
            return None
        data = json.loads(raw)
        return OTPRecord(
            phone_number=phone_number,
            otp_hash=data["otp_hash"],
            attempt_count=data["attempt_count"],
            last_sent_at=datetime.fromtimestamp(data["last_sent_at_ts"], tz=timezone.utc),
            expires_at=datetime.fromtimestamp(data["expires_at_ts"], tz=timezone.utc),
            used_at=(
                datetime.fromtimestamp(data["used_at_ts"], tz=timezone.utc)
                if data.get("used_at_ts")
                else None
            ),
        )

    async def increment_attempts(self, phone_number: str) -> int:
        key = self._key(phone_number)
        raw: str | None = await self._r.get(key)
        if not raw:
            return 0
        data = json.loads(raw)
        data["attempt_count"] += 1
        ttl: int = await self._r.ttl(key)
        await self._r.set(key, json.dumps(data), ex=max(ttl, 1))
        return data["attempt_count"]

    async def invalidate(self, phone_number: str) -> None:
        key = self._key(phone_number)
        raw: str | None = await self._r.get(key)
        if not raw:
            return
        data = json.loads(raw)
        data["used_at_ts"] = datetime.now(tz=timezone.utc).timestamp()
        # Set a very short TTL so the key disappears shortly
        await self._r.set(key, json.dumps(data), ex=5)
