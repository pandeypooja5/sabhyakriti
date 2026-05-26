from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.entities.tokens import RefreshToken


class ITokenRepository(ABC):
    @abstractmethod
    async def store(self, token: RefreshToken) -> None: ...

    @abstractmethod
    async def find_by_hash(self, token_hash: str) -> RefreshToken | None: ...

    @abstractmethod
    async def revoke(self, token_id: UUID) -> None: ...

    @abstractmethod
    async def revoke_all_for_user(self, user_id: UUID) -> None: ...
