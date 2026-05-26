"""Create order schema, sequence, tables and indexes.

Revision ID: 0001
Revises:
Create Date: 2026-05-21
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# The schema name must be quoted throughout because `order` is a SQL reserved word.
_SCHEMA = "order"


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # 1. Create the schema                                                 #
    # ------------------------------------------------------------------ #
    op.execute('CREATE SCHEMA IF NOT EXISTS "order"')

    # ------------------------------------------------------------------ #
    # 2. Create order number sequence                                      #
    # ------------------------------------------------------------------ #
    op.execute('CREATE SEQUENCE IF NOT EXISTS "order".order_seq START 1 INCREMENT 1')

    # ------------------------------------------------------------------ #
    # 3. updated_at trigger function                                       #
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE OR REPLACE FUNCTION "order".set_updated_at()
        RETURNS TRIGGER LANGUAGE plpgsql AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$
        """
    )

    # ------------------------------------------------------------------ #
    # 4. orders table                                                      #
    # ------------------------------------------------------------------ #
    op.create_table(
        "orders",
        sa.Column("order_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column("order_number", sa.String(30), nullable=False, unique=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("payment_method", sa.String(20), nullable=False),
        sa.Column("payment_reference", sa.String(128), nullable=True),
        sa.Column("shipping_address", postgresql.JSONB, nullable=False),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "discount_amount",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "shipping_charge",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "cgst_amount",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "sgst_amount",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("cancellation_reason", sa.Text, nullable=True),
        sa.Column(
            "confirmed_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column("shipped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema=_SCHEMA,
    )

    op.create_index(
        "ix_orders_user_id", "orders", ["user_id"], schema=_SCHEMA
    )
    op.create_index(
        "ix_orders_status", "orders", ["status"], schema=_SCHEMA
    )
    op.create_index(
        "ix_orders_created_at", "orders", ["created_at"], schema=_SCHEMA
    )

    op.execute(
        """
        CREATE TRIGGER trg_orders_updated_at
        BEFORE UPDATE ON "order".orders
        FOR EACH ROW EXECUTE FUNCTION "order".set_updated_at()
        """
    )

    # ------------------------------------------------------------------ #
    # 5. order_items table                                                 #
    # ------------------------------------------------------------------ #
    op.create_table(
        "order_items",
        sa.Column(
            "order_item_id", postgresql.UUID(as_uuid=True), primary_key=True
        ),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                f'{_SCHEMA}.orders.order_id', ondelete="CASCADE"
            ),
            nullable=False,
        ),
        sa.Column("product_id", sa.String(128), nullable=False),
        sa.Column("variant_id", sa.String(128), nullable=True),
        sa.Column("product_name", sa.String(300), nullable=False),
        sa.Column("product_image_url", sa.String(1000), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("discounted_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.Column(
            "hsn_code", sa.String(10), nullable=False, server_default="5208"
        ),
        sa.Column(
            "cgst_rate",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="2.50",
        ),
        sa.Column(
            "sgst_rate",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="2.50",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema=_SCHEMA,
    )

    op.create_index(
        "ix_order_items_order_id", "order_items", ["order_id"], schema=_SCHEMA
    )
    op.create_index(
        "ix_order_items_product_id",
        "order_items",
        ["product_id"],
        schema=_SCHEMA,
    )

    # ------------------------------------------------------------------ #
    # 6. addresses table                                                   #
    # ------------------------------------------------------------------ #
    op.create_table(
        "addresses",
        sa.Column(
            "address_id", postgresql.UUID(as_uuid=True), primary_key=True
        ),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column("full_name", sa.String(100), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("address_line1", sa.String(200), nullable=False),
        sa.Column(
            "address_line2", sa.String(200), nullable=False, server_default=""
        ),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("pincode", sa.String(10), nullable=False),
        sa.Column(
            "is_default",
            sa.Boolean,
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema=_SCHEMA,
    )

    op.create_index(
        "ix_addresses_user_id", "addresses", ["user_id"], schema=_SCHEMA
    )
    op.create_index(
        "ix_addresses_is_default",
        "addresses",
        ["user_id", "is_default"],
        schema=_SCHEMA,
    )

    op.execute(
        """
        CREATE TRIGGER trg_addresses_updated_at
        BEFORE UPDATE ON "order".addresses
        FOR EACH ROW EXECUTE FUNCTION "order".set_updated_at()
        """
    )

    # ------------------------------------------------------------------ #
    # 7. return_requests table                                             #
    # ------------------------------------------------------------------ #
    op.create_table(
        "return_requests",
        sa.Column(
            "return_request_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                f'{_SCHEMA}.orders.order_id', ondelete="RESTRICT"
            ),
            nullable=False,
            unique=True,
        ),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column(
            "refund_amount",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column("admin_notes", sa.Text, nullable=True),
        sa.Column("processed_by", sa.String(128), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "items_received_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "refund_initiated_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema=_SCHEMA,
    )

    op.create_index(
        "ix_return_requests_order_id",
        "return_requests",
        ["order_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_return_requests_user_id",
        "return_requests",
        ["user_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_return_requests_status",
        "return_requests",
        ["status"],
        schema=_SCHEMA,
    )

    op.execute(
        """
        CREATE TRIGGER trg_return_requests_updated_at
        BEFORE UPDATE ON "order".return_requests
        FOR EACH ROW EXECUTE FUNCTION "order".set_updated_at()
        """
    )

    # ------------------------------------------------------------------ #
    # 8. return_items table                                                #
    # ------------------------------------------------------------------ #
    op.create_table(
        "return_items",
        sa.Column(
            "return_item_id", postgresql.UUID(as_uuid=True), primary_key=True
        ),
        sa.Column(
            "return_request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                f'{_SCHEMA}.return_requests.return_request_id',
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "order_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                f'{_SCHEMA}.order_items.order_item_id',
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        schema=_SCHEMA,
    )

    op.create_index(
        "ix_return_items_return_request_id",
        "return_items",
        ["return_request_id"],
        schema=_SCHEMA,
    )


def downgrade() -> None:
    op.execute('DROP SCHEMA IF EXISTS "order" CASCADE')
