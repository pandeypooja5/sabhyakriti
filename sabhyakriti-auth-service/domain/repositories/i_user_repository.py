from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.entities.user import OAuthAccount, User


class IUserRepository(ABC):
    @abstractmethod
    async def find_by_id(self, user_id: UUID) -> User | None: ...

    @abstractmethod
    async def find_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def find_by_phone(self, phone_number: str) -> User | None: ...

    @abstractmethod
    async def create(self, user: User) -> User: ...

    @abstractmethod
    async def update(self, user: User) -> User: ...


class IOAuthAccountRepository(ABC):
    @abstractmethod
    async def find_by_provider(
        self, provider: str, provider_user_id: str
    ) -> OAuthAccount | None: ...

    @abstractmethod
    async def create(self, account: OAuthAccount) -> OAuthAccount: ...
