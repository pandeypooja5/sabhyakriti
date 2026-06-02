"""Internal service-to-service API router."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from application.dtos.product_dtos import ProductSummaryDTO, StockDeltaRequest
from application.services.product_application_service import ProductApplicationService
from presentation.dependencies import get_read_db, get_write_db, verify_internal_secret

router = APIRouter(prefix="/internal/v1", tags=["internal"])


class ProductBatchRequest(BaseModel):
    """Request body for batch product fetch."""
    product_ids: list[str]


class StockReserveRequest(BaseModel):
    """Request body for stock reserve/release (from Order Service)."""
    product_id: str
    delta: int
    variant_id: str | None = None


class ProductBatchItem(BaseModel):
    """Product info returned in batch."""
    product_id: str
    name: str
    slug: str = ""
    primary_image_url: str | None
    discounted_price: float
    stock_status: str
    is_active: bool


def _build_product_service(
    request: Request,
    write_session: AsyncSession,
    read_session: AsyncSession,
) -> ProductApplicationService:
    return request.app.state.service_factory.build_product_service(
        write_session, read_session
    )


@router.patch(
    "/products/{product_id}/stock",
    response_model=ProductSummaryDTO,
    summary="Reserve or release stock (internal, shared-secret protected)",
    dependencies=[Depends(verify_internal_secret)],
)
async def update_stock(
    product_id: UUID,
    body: StockDeltaRequest,
    request: Request,
    write_db: Annotated[AsyncSession, Depends(get_write_db)],
    read_db: Annotated[AsyncSession, Depends(get_read_db)],
) -> ProductSummaryDTO:
    """Positive delta = reserve (decrement), negative delta = release (increment)."""
    svc = _build_product_service(request, write_db, read_db)
    if body.delta > 0:
        return await svc.reserve_stock(product_id, body.delta)
    else:
        return await svc.release_stock(product_id, abs(body.delta))


@router.post(
    "/products/batch",
    response_model=list[ProductBatchItem],
    summary="Fetch multiple products by ID (for Cart Service pricing)",
    dependencies=[Depends(verify_internal_secret)],
)
async def get_products_batch(
    body: ProductBatchRequest,
    request: Request,
    read_db: Annotated[AsyncSession, Depends(get_read_db)],
) -> list[ProductBatchItem]:
    """Fetch product pricing and availability for a batch of product IDs."""
    svc = _build_product_service(request, None, read_db)
    product_ids = [UUID(pid) for pid in body.product_ids]
    products = await svc.get_products_batch(product_ids)
    return [
        ProductBatchItem(
            product_id=str(p.product_id),
            name=p.name,
            slug=p.slug,
            primary_image_url=(p.primary_image.cloudfront_url if p.primary_image else None),
            discounted_price=float(p.discounted_price),
            stock_status=(
                p.stock_status.value
                if hasattr(p.stock_status, "value")
                else str(p.stock_status)
            ),
            is_active=p.is_active,
        )
        for p in products
    ]


@router.post(
    "/stock/reserve",
    response_model=ProductSummaryDTO,
    summary="Reserve stock for an order (internal, shared-secret protected)",
    dependencies=[Depends(verify_internal_secret)],
)
async def reserve_stock(
    body: StockReserveRequest,
    request: Request,
    write_db: Annotated[AsyncSession, Depends(get_write_db)],
    read_db: Annotated[AsyncSession, Depends(get_read_db)],
) -> ProductSummaryDTO:
    """Reserve (decrement) stock for a product. Used by Order Service at checkout."""
    svc = _build_product_service(request, write_db, read_db)
    return await svc.reserve_stock(UUID(body.product_id), abs(body.delta))


@router.post(
    "/stock/release",
    response_model=ProductSummaryDTO,
    summary="Release reserved stock (internal, shared-secret protected)",
    dependencies=[Depends(verify_internal_secret)],
)
async def release_stock(
    body: StockReserveRequest,
    request: Request,
    write_db: Annotated[AsyncSession, Depends(get_write_db)],
    read_db: Annotated[AsyncSession, Depends(get_read_db)],
) -> ProductSummaryDTO:
    """Release (increment) previously reserved stock. Compensating transaction."""
    svc = _build_product_service(request, write_db, read_db)
    return await svc.release_stock(UUID(body.product_id), abs(body.delta))
