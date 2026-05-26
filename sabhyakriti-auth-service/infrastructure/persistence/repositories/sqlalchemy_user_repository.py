from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from domain.entities.user import OAuthAccount, User
from domain.repositories.i_user_repository import IOAuthAccountRepository, IUserRepository
from domain.value_objects import UserRole
from infrastructure.persistence.models import OAuthAccountModel, UserModel


def _model_to_user(m: UserModel) -> User:
    return User(
        user_id=m.user_id,
        email=m.email,
        phone_number=m.phone_number,
        hashed_password=m.hashed_password,
        full_name=m.full_name,
        profile_picture_url=m.profile_picture_url,
        role=UserRole(m.role),
        is_email_verified=m.is_email_verified,
        is_phone_verified=m.is_phone_verified,
        is_active=m.is_active,
        failed_login_attempts=m.failed_login_attempts,
        locked_until=m.locked_until,
        mfa_secret_encrypted=m.mfa_secret_encrypted,
        mfa_enabled=m.mfa_enabled,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _user_to_model(u: User, existing: UserModel | None = None) -> UserModel:
    m = existing or UserModel()
    m.user_id = u.user_id
    m.email = u.email
    m.phone_number = u.phone_number
    m.hashed_password = u.hashed_password
    m.full_name = u.full_name
    m.profile_picture_url = u.profile_picture_url
    m.role = str(u.role)
    m.is_email_verified = u.is_email_verified
    m.is_phone_verified = u.is_phone_verified
    m.is_active = u.is_active
    m.failed_login_attempts = u.failed_login_attempts
    m.locked_until = u.locked_until
    m.mfa_secret_encrypted = u.mfa_secret_encrypted
    m.mfa_enabled = u.mfa_enabled
    m.created_at = u.created_at
    m.updated_at = u.updated_at
    return m


def _model_to_oauth(m: OAuthAccountModel) -> OAuthAccount:
    return OAuthAccount(
        oauth_id=m.oauth_id,
        user_id=m.user_id,
        provider=m.provider,
        provider_user_id=m.provider_user_id,
        provider_email=m.provider_email,
        created_at=m.created_at,
    )


class SQLAlchemyUserRepository(IUserRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def find_by_id(self, user_id: uuid.UUID) -> User | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.user_id == user_id)
            )
            m = result.scalar_one_or_none()
            return _model_to_user(m) if m else None

    async def find_by_email(self, email: str) -> User | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.email == email.lower())
            )
            m = result.scalar_one_or_none()
            return _model_to_user(m) if m else None

    async def find_by_phone(self, phone_number: str) -> User | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.phone_number == phone_number)
            )
            m = result.scalar_one_or_none()
            return _model_to_user(m) if m else None

    async def create(self, user: User) -> User:
        async with self._session_factory() as session:
            async with session.begin():
                m = _user_to_model(user)
                session.add(m)
            await session.refresh(m)
            return _model_to_user(m)

    async def update(self, user: User) -> User:
        async with self._session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    select(UserModel).where(UserModel.user_id == user.user_id)
                )
                m = result.scalar_one()
                _user_to_model(user, existing=m)
            await session.refresh(m)
            return _model_to_user(m)


class SQLAlchemyOAuthAccountRepository(IOAuthAccountRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def find_by_provider(
        self, provider: str, provider_user_id: str
    ) -> OAuthAccount | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(OAuthAccountModel).where(
                    OAuthAccountModel.provider == provider,
                    OAuthAccountModel.provider_user_id == provider_user_id,
                )
            )
            m = result.scalar_one_or_none()
            return _model_to_oauth(m) if m else None

    async def create(self, account: OAuthAccount) -> OAuthAccount:
        async with self._session_factory() as session:
            async with session.begin():
                m = OAuthAccountModel(
                    oauth_id=account.oauth_id,
                    user_id=account.user_id,
                    provider=account.provider,
                    provider_user_id=account.provider_user_id,
                    provider_email=account.provider_email,
                    created_at=account.created_at,
                )
                session.add(m)
            await session.refresh(m)
            return _model_to_oauth(m)
