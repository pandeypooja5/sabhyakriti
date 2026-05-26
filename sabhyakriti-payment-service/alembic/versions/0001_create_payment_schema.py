"""Create payment schema, tables, indexes and updated_at trigger.

Revision ID: 0001
Revises:
Create Date: 2026-05-21 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

SCHEMA = "payment"


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Create schema
    # ------------------------------------------------------------------
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")

    # ------------------------------------------------------------------
    # 2. Create updated_at trigger function (schema-qualified)
    # ------------------------------------------------------------------
    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION {SCHEMA}.set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    # ------------------------------------------------------------------
    # 3. Create payments table
    # ------------------------------------------------------------------
    op.create_table(
        "payments",
        sa.Column("payment_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("method", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("razorpay_order_id", sa.String(100), nullable=True),
        sa.Column("razorpay_payment_id", sa.String(100), nullable=True),
        sa.Column("razorpay_signature", sa.String(255), nullable=True),
        sa.Column("attempt_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("first_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refund_id", sa.String(100), nullable=True),
        sa.Column("refund_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        schema=SCHEMA,
    )

    # Unique constraints
    op.create_unique_constraint(
        "uq_payments_order_id", "payments", ["order_id"], schema=SCHEMA
    )
    op.create_unique_constraint(
        "uq_payments_razorpay_payment_id",
        "payments",
        ["razorpay_payment_id"],
        schema=SCHEMA,
    )

    # Indexes
    op.create_index(
        "ix_payments_order_id", "payments", ["order_id"], schema=SCHEMA
    )
    op.create_index(
        "ix_payments_user_id", "payments", ["user_id"], schema=SCHEMA
    )
    op.create_index(
        "ix_payments_status", "payments", ["status"], schema=SCHEMA
    )
    op.create_index(
        "ix_payments_razorpay_order_id",
        "payments",
        ["razorpay_order_id"],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_payments_razorpay_payment_id",
        "payments",
        ["razorpay_payment_id"],
        schema=SCHEMA,
    )
    # Partial index for the auto-cancel query: status=CREATED and first_attempt_at IS NOT NULL
    op.execute(
        f"""
        CREATE INDEX ix_payments_stale_created
        ON {SCHEMA}.payments (first_attempt_at)
        WHERE status = 'CREATED' AND first_attempt_at IS NOT NULL;
        """
    )

    # updated_at trigger
    op.execute(
        f"""
        CREATE TRIGGER trg_payments_updated_at
        BEFORE UPDATE ON {SCHEMA}.payments
        FOR EACH ROW EXECUTE FUNCTION {SCHEMA}.set_updated_at();
        """
    )

    # ------------------------------------------------------------------
    # 4. Create webhook_events table
    # ------------------------------------------------------------------
    op.create_table(
        "webhook_events",
        sa.Column("event_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("razorpay_event_id", sa.String(100), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("processed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("razorpay_payment_id", sa.String(100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        schema=SCHEMA,
    )

    # Unique constraint — the idempotency key
    op.create_unique_constraint(
        "uq_webhook_events_razorpay_event_id",
        "webhook_events",
        ["razorpay_event_id"],
        schema=SCHEMA,
    )

    # Indexes
    op.create_index(
        "ix_webhook_events_razorpay_event_id",
        "webhook_events",
        ["razorpay_event_id"],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_webhook_events_event_type",
        "webhook_events",
        ["event_type"],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_webhook_events_razorpay_payment_id",
        "webhook_events",
        ["razorpay_payment_id"],
        schema=SCHEMA,
    )
    # Partial index for unprocessed events
    op.execute(
        f"""
        CREATE INDEX ix_webhook_events_unprocessed
        ON {SCHEMA}.webhook_events (created_at)
        WHERE processed = false;
        """
    )


def downgrade() -> None:
    op.execute(f"DROP TABLE IF EXISTS {SCHEMA}.webhook_events CASCADE")
    op.execute(f"DROP TABLE IF EXISTS {SCHEMA}.payments CASCADE")
    op.execute(f"DROP FUNCTION IF EXISTS {SCHEMA}.set_updated_at() CASCADE")
    op.execute(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE")
