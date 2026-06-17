"""Add care_instructions column to products table.

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-17 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("care_instructions", sa.Text, nullable=True),
        schema="product",
    )


def downgrade() -> None:
    op.drop_column("products", "care_instructions", schema="product")
