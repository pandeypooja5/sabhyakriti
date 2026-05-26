"""Create product schema with all tables, indexes, FTS trigger.

Revision ID: 0001
Revises:
Create Date: 2026-05-21 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR

# revision identifiers
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # ---------------------------------------------------------------
    # 1. Create schema
    # ---------------------------------------------------------------
    op.execute("CREATE SCHEMA IF NOT EXISTS product")

    # ---------------------------------------------------------------
    # 2. categories
    # ---------------------------------------------------------------
    op.create_table(
        "categories",
        sa.Column("category_id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(300), nullable=False, unique=True),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        schema="product",
    )
    op.create_index("ix_categories_type", "categories", ["type"], schema="product")
    op.create_index("ix_categories_slug", "categories", ["slug"],
                    unique=True, schema="product")

    # ---------------------------------------------------------------
    # 3. products
    # ---------------------------------------------------------------
    op.create_table(
        "products",
        sa.Column("product_id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("sku", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(300), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("discount_percentage", sa.Numeric(5, 2), nullable=False,
                  server_default="0.00"),
        sa.Column("stock_qty", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("average_rating", sa.Numeric(3, 2), nullable=False,
                  server_default="0.00"),
        sa.Column("review_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("search_vector", TSVECTOR, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        schema="product",
    )
    op.create_index("ix_products_sku", "products", ["sku"], unique=True, schema="product")
    op.create_index("ix_products_slug", "products", ["slug"], unique=True, schema="product")
    op.create_index("ix_products_is_active", "products", ["is_active"], schema="product")
    op.create_index("ix_products_created_at", "products", ["created_at"], schema="product")
    # GIN index for full-text search
    op.execute(
        "CREATE INDEX ix_products_search_vector "
        "ON product.products USING GIN(search_vector)"
    )

    # ---------------------------------------------------------------
    # 4. product_categories (junction table)
    # ---------------------------------------------------------------
    op.create_table(
        "product_categories",
        sa.Column("product_id", UUID(as_uuid=True),
                  sa.ForeignKey("product.products.product_id", ondelete="CASCADE"),
                  primary_key=True),
        sa.Column("category_id", UUID(as_uuid=True),
                  sa.ForeignKey("product.categories.category_id", ondelete="CASCADE"),
                  primary_key=True),
        schema="product",
    )
    op.create_index("ix_product_categories_product_id", "product_categories",
                    ["product_id"], schema="product")
    op.create_index("ix_product_categories_category_id", "product_categories",
                    ["category_id"], schema="product")

    # ---------------------------------------------------------------
    # 5. product_images
    # ---------------------------------------------------------------
    op.create_table(
        "product_images",
        sa.Column("image_id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("product_id", UUID(as_uuid=True),
                  sa.ForeignKey("product.products.product_id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("s3_key", sa.String(500), nullable=False),
        sa.Column("cloudfront_url", sa.Text, nullable=False),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        schema="product",
    )
    op.create_index("ix_product_images_product_id", "product_images",
                    ["product_id"], schema="product")
    # Partial unique index: only one primary image per product
    op.execute(
        "CREATE UNIQUE INDEX uix_product_images_primary "
        "ON product.product_images (product_id) "
        "WHERE is_primary = true"
    )

    # ---------------------------------------------------------------
    # 6. reviews
    # ---------------------------------------------------------------
    op.create_table(
        "reviews",
        sa.Column("review_id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("product_id", UUID(as_uuid=True),
                  sa.ForeignKey("product.products.product_id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("rating", sa.SmallInteger,
                  sa.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating"),
                  nullable=False),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("is_verified_purchase", sa.Boolean, nullable=False,
                  server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        schema="product",
    )
    op.create_index("ix_reviews_product_id", "reviews", ["product_id"], schema="product")
    op.create_index("ix_reviews_user_id", "reviews", ["user_id"], schema="product")
    op.create_index("uix_reviews_user_product", "reviews", ["user_id", "product_id"],
                    unique=True, schema="product")

    # ---------------------------------------------------------------
    # 7. FTS trigger function + trigger
    # ---------------------------------------------------------------
    op.execute(
        """
        CREATE OR REPLACE FUNCTION product.update_product_search_vector()
        RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('english', coalesce(NEW.name, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(NEW.description, '')), 'B') ||
                setweight(to_tsvector('english', coalesce(NEW.sku, '')), 'C');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_product_search_vector
        BEFORE INSERT OR UPDATE OF name, description, sku
        ON product.products
        FOR EACH ROW
        EXECUTE FUNCTION product.update_product_search_vector();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_product_search_vector ON product.products")
    op.execute("DROP FUNCTION IF EXISTS product.update_product_search_vector()")
    op.drop_table("reviews", schema="product")
    op.drop_table("product_images", schema="product")
    op.drop_table("product_categories", schema="product")
    op.drop_table("products", schema="product")
    op.drop_table("categories", schema="product")
    op.execute("DROP SCHEMA IF EXISTS product CASCADE")
