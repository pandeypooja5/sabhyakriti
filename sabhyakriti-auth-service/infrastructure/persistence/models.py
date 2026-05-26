from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import text

from infrastructure.persistence.database import Base

_SCHEMA = "auth"


class UserModel(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_auth_users_email", "email"),
        Index("ix_auth_users_phone_number", "phone_number"),
        Index("ix_auth_users_role", "role"),
        {"schema": _SCHEMA},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(15), unique=True, nullable=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    profile_picture_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'CUSTOMER'")
    )
    is_email_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    is_phone_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("0")
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    mfa_secret_encrypted: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mfa_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    oauth_accounts: Mapped[list[OAuthAccountModel]] = relationship(
        "OAuthAccountModel", back_populates="user", cascade="all, delete-orphan"
    )
    email_verification_tokens: Mapped[list[EmailVerificationTokenModel]] = relationship(
        "EmailVerificationTokenModel", back_populates="user", cascade="all, delete-orphan"
    )
    password_reset_tokens: Mapped[list[PasswordResetTokenModel]] = relationship(
        "PasswordResetTokenModel", back_populates="user", cascade="all, delete-orphan"
    )


class OAuthAccountModel(Base):
    __tablename__ = "oauth_accounts"
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_user"),
        Index("ix_auth_oauth_accounts_user_id", "user_id"),
        {"schema": _SCHEMA},
    )

    oauth_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{_SCHEMA}.users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped[UserModel] = relationship("UserModel", back_populates="oauth_accounts")


class EmailVerificationTokenModel(Base):
    __tablename__ = "email_verification_tokens"
    __table_args__ = (
        Index("ix_auth_evtoken_user_id", "user_id"),
        Index("ix_auth_evtoken_token_hash", "token_hash"),
        {"schema": _SCHEMA},
    )

    token_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{_SCHEMA}.users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[UserModel] = relationship(
        "UserModel", back_populates="email_verification_tokens"
    )


class PasswordResetTokenModel(Base):
    __tablename__ = "password_reset_tokens"
    __table_args__ = (
        Index("ix_auth_prtoken_user_id", "user_id"),
        Index("ix_auth_prtoken_token_hash", "token_hash"),
        {"schema": _SCHEMA},
    )

    token_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{_SCHEMA}.users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[UserModel] = relationship(
        "UserModel", back_populates="password_reset_tokens"
    )
