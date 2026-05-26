from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from domain.entities.tokens import EmailVerificationToken, PasswordResetToken
from domain.repositories.i_verification_repository import (
    IEmailVerificationRepository,
    IPasswordResetRepository,
)
from infrastructure.persistence.models import (
    EmailVerificationTokenModel,
    PasswordResetTokenModel,
)


def _model_to_ev(m: EmailVerificationTokenModel) -> EmailVerificationToken:
    return EmailVerificationToken(
        token_id=m.token_id,
        user_id=m.user_id,
        token_hash=m.token_hash,
        expires_at=m.expires_at,
        created_at=m.created_at,
        used_at=m.used_at,
    )


def _model_to_pr(m: PasswordResetTokenModel) -> PasswordResetToken:
    return PasswordResetToken(
        token_id=m.token_id,
        user_id=m.user_id,
        token_hash=m.token_hash,
        expires_at=m.expires_at,
        created_at=m.created_at,
        used_at=m.used_at,
    )


class SQLAlchemyEmailVerificationRepository(IEmailVerificationRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(self, token: EmailVerificationToken) -> None:
        async with self._session_factory() as session:
            async with session.begin():
                m = EmailVerificationTokenModel(
                    token_id=token.token_id,
                    user_id=token.user_id,
                    token_hash=token.token_hash,
                    expires_at=token.expires_at,
                    created_at=token.created_at,
                    used_at=token.used_at,
                )
                session.add(m)

    async def find_by_hash(self, token_hash: str) -> EmailVerificationToken | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(EmailVerificationTokenModel).where(
                    EmailVerificationTokenModel.token_hash == token_hash
                )
            )
            m = result.scalar_one_or_none()
            return _model_to_ev(m) if m else None

    async def mark_used(self, token_id: uuid.UUID) -> None:
        from datetime import datetime, timezone

        async with self._session_factory() as session:
            async with session.begin():
                await session.execute(
                    update(EmailVerificationTokenModel)
                    .where(EmailVerificationTokenModel.token_id == token_id)
                    .values(used_at=datetime.now(tz=timezone.utc))
                )


class SQLAlchemyPasswordResetRepository(IPasswordResetRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(self, token: PasswordResetToken) -> None:
        async with self._session_factory() as session:
            async with session.begin():
                m = PasswordResetTokenModel(
                    token_id=token.token_id,
                    user_id=token.user_id,
                    token_hash=token.token_hash,
                    expires_at=token.expires_at,
                    created_at=token.created_at,
                    used_at=token.used_at,
                )
                session.add(m)

    async def find_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(PasswordResetTokenModel).where(
                    PasswordResetTokenModel.token_hash == token_hash
                )
            )
            m = result.scalar_one_or_none()
            return _model_to_pr(m) if m else None

    async def invalidate_existing_for_user(self, user_id: uuid.UUID) -> None:
        from datetime import datetime, timezone

        async with self._session_factory() as session:
            async with session.begin():
                await session.execute(
                    update(PasswordResetTokenModel)
                    .where(
                        PasswordResetTokenModel.user_id == user_id,
                        PasswordResetTokenModel.used_at.is_(None),
                    )
                    .values(used_at=datetime.now(tz=timezone.utc))
                )

    async def mark_used(self, token_id: uuid.UUID) -> None:
        from datetime import datetime, timezone

        async with self._session_factory() as session:
            async with session.begin():
                await session.execute(
                    update(PasswordResetTokenModel)
                    .where(PasswordResetTokenModel.token_id == token_id)
                    .values(used_at=datetime.now(tz=timezone.utc))
                )
