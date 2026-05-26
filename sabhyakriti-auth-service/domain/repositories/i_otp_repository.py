from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities.otp_record import OTPRecord


class IOTPRepository(ABC):
    @abstractmethod
    async def upsert(self, record: OTPRecord) -> None: ...

    @abstractmethod
    async def find_by_phone(self, phone_number: str) -> OTPRecord | None: ...

    @abstractmethod
    async def increment_attempts(self, phone_number: str) -> int: ...

    @abstractmethod
    async def invalidate(self, phone_number: str) -> None: ...
