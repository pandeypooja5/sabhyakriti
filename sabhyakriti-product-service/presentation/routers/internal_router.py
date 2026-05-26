"""Internal service-to-service API router."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from application.dtos.product_dtos import ProductSummaryDTO, StockDeltaRequest
from application.services.product_application_service import ProductApplicationService
from presentation.dependencies import get_read_db, get_write_db, verify_internal_secret

router = APIRouter(prefix="/internal/v1", tags=["internal"])


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
