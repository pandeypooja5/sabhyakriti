"""Create notification schema and notification_logs table.

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""

from __future__ import annotations

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS notification")

    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_namespace n ON t.typnamespace=n.oid
                           WHERE t.typname='notification_type_enum' AND n.nspname='notification') THEN
                CREATE TYPE notification.notification_type_enum AS ENUM (
                    'EMAIL_VERIFICATION','PASSWORD_RESET','ORDER_CONFIRMATION','ORDER_SHIPPED',
                    'ORDER_DELIVERED','ORDER_CANCELLED','RETURN_RECEIVED','RETURN_APPROVED',
                    'REFUND_PROCESSED','PAYMENT_RECEIPT','SMS_OTP','SMS_ORDER_SHIPPED','SMS_ORDER_DELIVERED'
                );
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_namespace n ON t.typnamespace=n.oid
                           WHERE t.typname='notification_channel_enum' AND n.nspname='notification') THEN
                CREATE TYPE notification.notification_channel_enum AS ENUM ('EMAIL','SMS');
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_namespace n ON t.typnamespace=n.oid
                           WHERE t.typname='notification_status_enum' AND n.nspname='notification') THEN
                CREATE TYPE notification.notification_status_enum AS ENUM ('SENT','FAILED');
            END IF;
        END $$;
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS notification.notification_logs (
            id            UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
            notification_type notification.notification_type_enum NOT NULL,
            channel       notification.notification_channel_enum NOT NULL,
            recipient     VARCHAR(320) NOT NULL,
            status        notification.notification_status_enum NOT NULL,
            provider      VARCHAR(50) NOT NULL,
            error_message TEXT,
            created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("CREATE INDEX IF NOT EXISTS ix_notification_logs_type ON notification.notification_logs(notification_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_notification_logs_channel ON notification.notification_logs(channel)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_notification_logs_status ON notification.notification_logs(status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_notification_logs_created ON notification.notification_logs(created_at DESC)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_notification_logs_composite ON notification.notification_logs(status, notification_type, created_at DESC)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS notification.notification_logs")
    op.execute("DROP TYPE IF EXISTS notification.notification_status_enum")
    op.execute("DROP TYPE IF EXISTS notification.notification_channel_enum")
    op.execute("DROP TYPE IF EXISTS notification.notification_type_enum")
    op.execute("DROP SCHEMA IF EXISTS notification CASCADE")
