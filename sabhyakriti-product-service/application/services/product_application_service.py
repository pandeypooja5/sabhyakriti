"""Product application service — orchestrates all product-related use-cases."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

import bleach
import structlog

from application.clients.order_service_client import OrderServiceClient
from application.dtos.product_dtos import (
    BulkImportResultDTO,
    CategoryDTO,
    ConfirmImageUploadRequest,
    CreateProductRequest,
    PagedProductListDTO,
    PagedReviewsDTO,
    PresignedUrlDTO,
    ProductDetailDTO,
    ProductImageDTO,
    ProductSummaryDTO,
    ReviewDTO,
    UpdateProductRequest,
)
from domain.entities.product import Product, ProductImage
from domain.repositories.i_category_repository import ICategoryRepository
from domain.repositories.i_image_repository import IImageRepository
from domain.repositories.i_plp_cache_repository import IPlpCacheRepository
from domain.repositories.i_product_repository import IProductRepository
from domain.repositories.i_review_repository import IReviewRepository
from domain.services.slug_service import generate_slug, make_unique_slug
from domain.value_objects import CategoryType, SortOrder, StockStatus
from infrastructure.adapters.aws_cloudfront_adapter import build_cdn_url
from infrastructure.adapters.aws_s3_adapter import AWSS3Adapter

logger = structlog.get_logger(__name__)

_PLP_TTL = 300  # seconds
_MAX_IMAGES = 10
_ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
_ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}
_MAX_BULK_ROWS = 500
_PRESIGNED_TTL = 900  # 15 minutes


def _make_cache_key(params: dict[str, Any]) -> str:
    """SHA-256 hash of sorted query params for PLP cache key."""
    serialised = json.dumps(params, sort_keys=True, default=str)
    digest = hashlib.sha256(serialised.encode()).hexdigest()
    return f"product_plp:{digest}"


def _sanitise_description(raw: str) -> str:
    """Strip all HTML tags from product description."""
    return bleach.clean(raw, tags=[], strip=True)


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class ProductApplicationService:
    """Implements all product-related application use-cases."""

    def __init__(
        self,
        product_repo: IProductRepository,
        category_repo: ICategoryRepository,
        image_repo: IImageRepository,
        review_repo: IReviewRepository,
        plp_cache: IPlpCacheRepository,
        s3_adapter: AWSS3Adapter,
        cloudfront_domain: str,
        s3_bucket: str,
    ) -> None:
        self._products = product_repo
        self._categories = category_repo
        self._images = image_repo
        self._reviews = review_repo
        self._cache = plp_cache
        self._s3 = s3_adapter
        self._cdn_domain = cloudfront_domain
        self._s3_bucket = s3_bucket

    # ------------------------------------------------------------------
    # List products (PLP)
    # ------------------------------------------------------------------

    async def list_products(
        self,
        *,
        fabric_ids: list[UUID] | None = None,
        occasion_ids: list[UUID] | None = None,
        region_ids: list[UUID] | None = None,
        search: str | None = None,
        sort: SortOrder = SortOrder.NEWEST,
        page: int = 1,
        page_size: int = 24,
    ) -> PagedProductListDTO:
        page_size = min(page_size, 48)
        params: dict[str, Any] = {
            "fabric_ids": [str(i) for i in (fabric_ids or [])],
            "occasion_ids": [str(i) for i in (occasion_ids or [])],
            "region_ids": [str(i) for i in (region_ids or [])],
            "search": search,
            "sort": sort,
            "page": page,
            "page_size": page_size,
        }
        cache_key = _make_cache_key(params)

        cached = await self._cache.get(cache_key)
        if cached is not None:
            logger.debug("plp_cache_hit", key=cache_key)
            return PagedProductListDTO(**cached)

        products, total = await self._products.list_products(
            fabric_ids=fabric_ids,
            occasion_ids=occasion_ids,
            region_ids=region_ids,
            search=search,
            sort=sort,
            page=page,
            page_size=page_size,
        )

        items = [self._to_summary_dto(p) for p in products]
        total_pages = max(1, -(-total // page_size))  # ceiling division
        result = PagedProductListDTO(
            items=items,
            total_count=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

        await self._cache.set(cache_key, result.model_dump(mode="json"), ttl=_PLP_TTL)
        return result

    # ------------------------------------------------------------------
    # Product detail
    # ------------------------------------------------------------------

    async def get_product_detail(self, product_id: UUID) -> ProductDetailDTO:
        product = await self._products.get_by_id(product_id)
        if product is None:
            raise LookupError(f"Product {product_id} not found")
        return await self._build_detail_dto(product)

    async def get_product_by_slug(self, slug: str) -> ProductDetailDTO:
        product = await self._products.get_by_slug(slug)
        if product is None:
            raise LookupError(f"Product with slug '{slug}' not found")
        return await self._build_detail_dto(product)

    async def _build_detail_dto(self, product: Product) -> ProductDetailDTO:
        images = await self._images.list_for_product(product.product_id)
        raw_categories = await self._categories.get_categories_for_product(
            product.product_id
        )
        related = await self._products.get_related_products(product.product_id)
        reviews_list, review_total = await self._reviews.list_for_product(
            product.product_id, page=1, page_size=10
        )

        categories_by_type: dict[str, list[CategoryDTO]] = {
            t.value: [] for t in CategoryType
        }
        for cat in raw_categories:
            categories_by_type[cat.type.value].append(
                CategoryDTO.model_validate(cat)
            )

        image_dtos = [ProductImageDTO.model_validate(img) for img in images]
        review_dtos = [ReviewDTO.model_validate(r) for r in reviews_list]
        related_dtos = [self._to_summary_dto(p) for p in related]

        return ProductDetailDTO(
            product_id=product.product_id,
            sku=product.sku,
            name=product.name,
            slug=product.slug,
            description=product.description,
            price=product.price,
            discount_percentage=product.discount_percentage,
            discounted_price=product.discounted_price,
            savings_amount=product.savings_amount,
            stock_qty=product.stock_qty,
            stock_status=product.stock_status,
            fabric=product.fabric,
            color=product.color,
            work=product.work,
            saree_length=product.saree_length,
            blouse_length=product.blouse_length,
            blouse_included=product.blouse_included,
            average_rating=product.average_rating,
            review_count=product.review_count,
            is_active=product.is_active,
            created_at=product.created_at,
            updated_at=product.updated_at,
            images=image_dtos,
            categories=categories_by_type,
            reviews=PagedReviewsDTO(
                items=review_dtos,
                total_count=review_total,
                page=1,
                page_size=10,
                total_pages=max(1, -(-review_total // 10)),
            ),
            related_products=related_dtos,
        )

    # ------------------------------------------------------------------
    # Image management
    # ------------------------------------------------------------------

    async def get_presigned_upload_url(
        self, product_id: UUID, filename: str, content_type: str
    ) -> PresignedUrlDTO:
        # Validate product exists
        product = await self._products.get_by_id(product_id)
        if product is None:
            raise LookupError(f"Product {product_id} not found")

        # Validate extension
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in _ALLOWED_IMAGE_EXTENSIONS:
            raise ValueError(
                f"File extension '{ext}' not allowed. Allowed: {_ALLOWED_IMAGE_EXTENSIONS}"
            )

        # Validate image count
        count = await self._images.count_for_product(product_id)
        if count >= _MAX_IMAGES:
            raise ValueError(f"Product already has {_MAX_IMAGES} images (max)")

        s3_key = f"products/{product_id}/{uuid.uuid4()}.{ext}"
        presigned_url = self._s3.generate_presigned_put_url(
            s3_key=s3_key,
            ttl_seconds=_PRESIGNED_TTL,
            content_type=content_type,
        )
        return PresignedUrlDTO(
            presigned_url=presigned_url,
            s3_key=s3_key,
            expires_in=_PRESIGNED_TTL,
        )

    async def confirm_image_upload(
        self,
        product_id: UUID,
        request: ConfirmImageUploadRequest,
    ) -> ProductImageDTO:
        # Validate product exists
        product = await self._products.get_by_id(product_id)
        if product is None:
            raise LookupError(f"Product {product_id} not found")

        # Validate s3_key belongs to this product
        expected_prefix = f"products/{product_id}/"
        if not request.s3_key.startswith(expected_prefix):
            raise ValueError("s3_key does not belong to this product")

        if request.is_primary:
            await self._images.clear_primary_flag(product_id)

        cdn_url = build_cdn_url(request.s3_key, self._cdn_domain)
        image = ProductImage(
            image_id=uuid.uuid4(),
            product_id=product_id,
            s3_key=request.s3_key,
            cloudfront_url=cdn_url,
            is_primary=request.is_primary,
            sort_order=request.sort_order,
            created_at=_utcnow(),
        )
        saved = await self._images.create(image)
        return ProductImageDTO.model_validate(saved)

    async def delete_image(self, product_id: UUID, image_id: UUID) -> None:
        image = await self._images.get_by_id(image_id)
        if image is None or image.product_id != product_id:
            raise LookupError(f"Image {image_id} not found on product {product_id}")

        was_primary = image.is_primary
        self._s3.delete_object(image.s3_key)
        await self._images.delete(image_id)

        if was_primary:
            await self._images.promote_first_as_primary(product_id)

    # ------------------------------------------------------------------
    # Admin CRUD
    # ------------------------------------------------------------------

    async def create_product(self, request: CreateProductRequest) -> ProductDetailDTO:
        sanitised_desc = _sanitise_description(request.description)
        base_slug = generate_slug(request.name)
        existing_slugs = await self._products.get_slug_set()
        slug = make_unique_slug(base_slug, existing_slugs)

        now = _utcnow()
        product = Product(
            product_id=uuid.uuid4(),
            sku=request.sku,
            name=request.name,
            slug=slug,
            description=sanitised_desc,
            price=request.price,
            discount_percentage=request.discount_percentage,
            stock_qty=request.stock_qty,
            is_active=True,
            fabric=request.fabric,
            color=request.color,
            work=request.work,
            saree_length=request.saree_length,
            blouse_length=request.blouse_length,
            blouse_included=request.blouse_included,
            average_rating=Decimal("0.00"),
            review_count=0,
            created_at=now,
            updated_at=now,
            category_ids=request.category_ids,
        )

        saved = await self._products.create(product)
        await self._cache.invalidate_all()
        # Re-fetch via read session so images/categories are loaded without
        # triggering MissingGreenlet on the write session.
        fetched = await self._products.get_by_id(saved.product_id)
        return await self._build_detail_dto(fetched if fetched else saved)

    async def update_product(
        self, product_id: UUID, request: UpdateProductRequest
    ) -> ProductDetailDTO:
        updates: dict[str, Any] = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = _sanitise_description(request.description)
        if request.price is not None:
            updates["price"] = request.price
        if request.discount_percentage is not None:
            updates["discount_percentage"] = request.discount_percentage
        if request.stock_qty is not None:
            updates["stock_qty"] = request.stock_qty
        if request.fabric is not None:
            updates["fabric"] = request.fabric
        if request.color is not None:
            updates["color"] = request.color
        if request.work is not None:
            updates["work"] = request.work
        if request.saree_length is not None:
            updates["saree_length"] = request.saree_length
        if request.blouse_length is not None:
            updates["blouse_length"] = request.blouse_length
        if request.blouse_included is not None:
            updates["blouse_included"] = request.blouse_included
        if request.category_ids is not None:
            updates["category_ids"] = request.category_ids
        if request.is_active is not None:
            updates["is_active"] = request.is_active
        updates["updated_at"] = _utcnow()

        updated = await self._products.update(product_id, updates)
        await self._cache.invalidate_all()
        return await self._build_detail_dto(updated)

    async def soft_delete_product(self, product_id: UUID) -> None:
        await self._products.soft_delete(product_id)
        await self._cache.invalidate_all()

    # ------------------------------------------------------------------
    # Stock operations (internal)
    # ------------------------------------------------------------------

    async def reserve_stock(self, product_id: UUID, delta: int) -> ProductSummaryDTO:
        product = await self._products.reserve_stock(product_id, abs(delta))
        await self._cache.invalidate_all()
        return self._to_summary_dto(product)

    async def release_stock(self, product_id: UUID, delta: int) -> ProductSummaryDTO:
        product = await self._products.release_stock(product_id, abs(delta))
        await self._cache.invalidate_all()
        return self._to_summary_dto(product)

    # ------------------------------------------------------------------
    # Bulk import
    # ------------------------------------------------------------------

    async def bulk_import(self, csv_bytes: bytes) -> BulkImportResultDTO:
        content = csv_bytes.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        if len(rows) > _MAX_BULK_ROWS:
            raise ValueError(
                f"CSV exceeds max row limit of {_MAX_BULK_ROWS}. Got {len(rows)} rows."
            )

        imported_count = 0
        updated_count = 0
        failed_rows: list[dict[str, Any]] = []

        for idx, row in enumerate(rows, start=2):  # row 1 = header
            try:
                sku = row.get("sku", "").strip()
                if not sku:
                    raise ValueError("sku is required")

                name = row.get("name", "").strip()
                if not name:
                    raise ValueError("name is required")

                price = Decimal(row.get("price", "0"))
                discount_pct = Decimal(row.get("discount_percentage", "0"))
                stock_qty = int(row.get("stock_qty", "0"))
                description = _sanitise_description(row.get("description", ""))

                # Check if SKU exists already — attempt update
                existing = await self._products.list_products(
                    page=1, page_size=1, search=sku
                )
                # Simple search won't guarantee SKU match; we need get_by_sku
                # Fallback: check via create/update pattern
                request = CreateProductRequest(
                    sku=sku,
                    name=name,
                    description=description,
                    price=price,
                    discount_percentage=discount_pct,
                    stock_qty=stock_qty,
                )
                await self.create_product(request)
                imported_count += 1

            except Exception as exc:  # noqa: BLE001
                failed_rows.append({"row": idx, "error": str(exc), "data": dict(row)})

        await self._cache.invalidate_all()
        return BulkImportResultDTO(
            imported_count=imported_count,
            updated_count=updated_count,
            failed_rows=failed_rows,
        )

    # ------------------------------------------------------------------
    # Internal: Batch operations for other services
    # ------------------------------------------------------------------

    async def get_products_batch(self, product_ids: list[UUID]) -> list[Product]:
        """Fetch multiple product entities by ID for internal service use (e.g., Cart Service).

        Returns domain entities so callers have access to all fields
        (including is_active and primary_image), not just summary DTO fields.
        """
        return await self._products.find_by_ids(product_ids)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _to_summary_dto(self, product: Product) -> ProductSummaryDTO:
        primary_image = product.primary_image
        return ProductSummaryDTO(
            product_id=product.product_id,
            name=product.name,
            slug=product.slug,
            sku=product.sku,
            discounted_price=product.discounted_price,
            price=product.price,
            discount_percentage=product.discount_percentage,
            savings_amount=product.savings_amount,
            stock_status=product.stock_status,
            stock_qty=product.stock_qty,
            primary_image_url=primary_image.cloudfront_url if primary_image else None,
            average_rating=product.average_rating,
            review_count=product.review_count,
        )
