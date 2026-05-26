"""Bulk product import router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from application.dtos.product_dtos import BulkImportResultDTO
from application.services.product_application_service import ProductApplicationService
from presentation.dependencies import CurrentUser, get_read_db, get_write_db, require_admin

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

_MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB


def _build_product_service(
    request: Request,
    write_session: AsyncSession,
    read_session: AsyncSession,
) -> ProductApplicationService:
    return request.app.state.service_factory.build_product_service(
        write_session, read_session
    )


@router.post(
    "/products/bulk-import",
    response_model=BulkImportResultDTO,
    summary="Bulk import products from CSV (admin)",
)
async def bulk_import_products(
    request: Request,
    write_db: Annotated[AsyncSession, Depends(get_write_db)],
    read_db: Annotated[AsyncSession, Depends(get_read_db)],
    file: Annotated[UploadFile, File(description="CSV file; max 500 rows")],
    _admin: Annotated[CurrentUser, Depends(require_admin)],
) -> BulkImportResultDTO:
    if file.content_type not in (
        "text/csv",
        "application/csv",
        "application/octet-stream",
    ):
        raise ValueError("Invalid file type. Please upload a CSV file.")

    csv_bytes = await file.read(_MAX_UPLOAD_BYTES + 1)
    if len(csv_bytes) > _MAX_UPLOAD_BYTES:
        raise ValueError(
            f"CSV file exceeds maximum allowed size of {_MAX_UPLOAD_BYTES // 1024} KB"
        )

    svc = _build_product_service(request, write_db, read_db)
    return await svc.bulk_import(csv_bytes)
