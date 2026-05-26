from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.entities.tokens import EmailVerificationToken, PasswordResetToken


class IEmailVerificationRepository(ABC):
    @abstractmethod
    async def create(self, token: EmailVerificationToken) -> None: ...

    @abstractmethod
    async def find_by_hash(self, token_hash: str) -> EmailVerificationToken | None: ...

    @abstractmethod
    async def mark_used(self, token_id: UUID) -> None: ...


class IPasswordResetRepository(ABC):
    @abstractmethod
    async def create(self, token: PasswordResetToken) -> None: ...

    @abstractmethod
    async def find_by_hash(self, token_hash: str) -> PasswordResetToken | None: ...

    @abstractmethod
    async def invalidate_existing_for_user(self, user_id: UUID) -> None: ...

    @abstractmethod
    async def mark_used(self, token_id: UUID) -> None: ...
