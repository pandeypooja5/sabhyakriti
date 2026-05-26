"""Create cart schema with all tables, indexes, and constraints.

Revision ID: 0001
Revises:
Create Date: 2026-05-21
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

_SCHEMA = "cart"


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Create schema
    # ------------------------------------------------------------------
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {_SCHEMA}")

    # ------------------------------------------------------------------
    # 2. carts table
    # ------------------------------------------------------------------
    op.create_table(
        "carts",
        sa.Column(
            "cart_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "applied_coupon_code",
            sa.String(50),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", name="uq_carts_user_id"),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_carts_user_id",
        "carts",
        ["user_id"],
        unique=True,
        schema=_SCHEMA,
    )

    # ------------------------------------------------------------------
    # 3. cart_items table
    # ------------------------------------------------------------------
    op.create_table(
        "cart_items",
        sa.Column(
            "cart_item_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "cart_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(f"{_SCHEMA}.carts.cart_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "quantity",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "cart_id", "product_id", name="uq_cart_items_cart_product"
        ),
        sa.CheckConstraint(
            "quantity >= 1 AND quantity <= 10",
            name="ck_cart_items_quantity",
        ),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_cart_items_cart_id",
        "cart_items",
        ["cart_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_cart_items_product_id",
        "cart_items",
        ["product_id"],
        schema=_SCHEMA,
    )

    # ------------------------------------------------------------------
    # 4. wishlists table
    # ------------------------------------------------------------------
    op.create_table(
        "wishlists",
        sa.Column(
            "wishlist_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", name="uq_wishlists_user_id"),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_wishlists_user_id",
        "wishlists",
        ["user_id"],
        unique=True,
        schema=_SCHEMA,
    )

    # ------------------------------------------------------------------
    # 5. wishlist_items table
    # ------------------------------------------------------------------
    op.create_table(
        "wishlist_items",
        sa.Column(
            "wishlist_item_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "wishlist_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                f"{_SCHEMA}.wishlists.wishlist_id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "wishlist_id",
            "product_id",
            name="uq_wishlist_items_wishlist_product",
        ),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_wishlist_items_wishlist_id",
        "wishlist_items",
        ["wishlist_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_wishlist_items_product_id",
        "wishlist_items",
        ["product_id"],
        schema=_SCHEMA,
    )

    # ------------------------------------------------------------------
    # 6. coupons table
    # ------------------------------------------------------------------
    op.create_table(
        "coupons",
        sa.Column(
            "coupon_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("coupon_type", sa.String(10), nullable=False),
        sa.Column(
            "value",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
        ),
        sa.Column(
            "min_order_amount",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column(
            "used_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("TRUE"),
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.UniqueConstraint("code", name="uq_coupons_code"),
        sa.CheckConstraint("value > 0", name="ck_coupons_value_positive"),
        sa.CheckConstraint(
            "min_order_amount >= 0", name="ck_coupons_min_order_non_negative"
        ),
        sa.CheckConstraint(
            "used_count >= 0", name="ck_coupons_used_count_non_negative"
        ),
        sa.CheckConstraint(
            "coupon_type IN ('FLAT', 'PERCENT')",
            name="ck_coupons_type_valid",
        ),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_coupons_code",
        "coupons",
        ["code"],
        unique=True,
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_coupons_is_active",
        "coupons",
        ["is_active"],
        schema=_SCHEMA,
    )

    # ------------------------------------------------------------------
    # 7. Trigger: auto-update updated_at on carts and wishlists
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE OR REPLACE FUNCTION cart.set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    for table in ("carts", "wishlists", "coupons"):
        op.execute(
            f"""
            CREATE TRIGGER trg_{table}_updated_at
            BEFORE UPDATE ON {_SCHEMA}.{table}
            FOR EACH ROW EXECUTE FUNCTION {_SCHEMA}.set_updated_at();
            """
        )


def downgrade() -> None:
    op.execute(f"DROP SCHEMA IF EXISTS {_SCHEMA} CASCADE")
