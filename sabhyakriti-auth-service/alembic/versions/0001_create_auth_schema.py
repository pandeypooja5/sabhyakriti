"""create auth schema and initial tables

Revision ID: 0001
Revises:
Create Date: 2026-05-21 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Schema ────────────────────────────────────────────────────────────────
    op.execute("CREATE SCHEMA IF NOT EXISTS auth")

    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=True, unique=True),
        sa.Column("phone_number", sa.String(15), nullable=True, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("full_name", sa.String(100), nullable=False),
        sa.Column("profile_picture_url", sa.String(500), nullable=True),
        sa.Column(
            "role",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'CUSTOMER'"),
        ),
        sa.Column(
            "is_email_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "is_phone_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "failed_login_attempts",
            sa.SmallInteger(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mfa_secret_encrypted", sa.String(255), nullable=True),
        sa.Column(
            "mfa_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        schema="auth",
    )
    op.create_index(
        "ix_auth_users_email", "users", ["email"], schema="auth"
    )
    op.create_index(
        "ix_auth_users_phone_number", "users", ["phone_number"], schema="auth"
    )
    op.create_index(
        "ix_auth_users_role", "users", ["role"], schema="auth"
    )

    # ── oauth_accounts ────────────────────────────────────────────────────────
    op.create_table(
        "oauth_accounts",
        sa.Column("oauth_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("provider_user_id", sa.String(255), nullable=False),
        sa.Column("provider_email", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_user"),
        schema="auth",
    )
    op.create_index(
        "ix_auth_oauth_accounts_user_id", "oauth_accounts", ["user_id"], schema="auth"
    )

    # ── email_verification_tokens ─────────────────────────────────────────────
    op.create_table(
        "email_verification_tokens",
        sa.Column("token_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        schema="auth",
    )
    op.create_index(
        "ix_auth_evtoken_user_id", "email_verification_tokens", ["user_id"], schema="auth"
    )
    op.create_index(
        "ix_auth_evtoken_token_hash", "email_verification_tokens", ["token_hash"], schema="auth"
    )

    # ── password_reset_tokens ─────────────────────────────────────────────────
    op.create_table(
        "password_reset_tokens",
        sa.Column("token_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        schema="auth",
    )
    op.create_index(
        "ix_auth_prtoken_user_id", "password_reset_tokens", ["user_id"], schema="auth"
    )
    op.create_index(
        "ix_auth_prtoken_token_hash", "password_reset_tokens", ["token_hash"], schema="auth"
    )


def downgrade() -> None:
    op.drop_table("password_reset_tokens", schema="auth")
    op.drop_table("email_verification_tokens", schema="auth")
    op.drop_table("oauth_accounts", schema="auth")
    op.drop_table("users", schema="auth")
    op.execute("DROP SCHEMA IF EXISTS auth CASCADE")
