"""Product API router."""
from __future__ import annotations
import os
import uuid as _uuid
from fastapi.responses import Response, JSONResponse

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from application.dtos.product_dtos import (
    ConfirmImageUploadRequest,
    CreateProductRequest,
    PagedProductListDTO,
    PresignedUrlDTO,
    ProductDetailDTO,
    UpdateProductRequest,
)
from application.services.product_application_service import ProductApplicationService
from domain.value_objects import SortOrder
from presentation.dependencies import (
    CurrentUser,
    get_read_db,
    get_write_db,
    require_admin,
)

router = APIRouter(prefix="/api/v1/products", tags=["products"])


def _build_product_service(
    request: Request,
    write_session: AsyncSession,
    read_session: AsyncSession,
) -> ProductApplicationService:
    return request.app.state.service_factory.build_product_service(
        write_session, read_session
    )


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------


def _parse_uuid_csv(raw: str | None) -> list[UUID] | None:
    """Parse a comma-separated list of UUIDs (or repeated/[]-style values)."""
    if not raw:
        return None
    result: list[UUID] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            result.append(UUID(part))
        except ValueError:
            continue
    return result or None


@router.get("", response_model=PagedProductListDTO, summary="List products (PLP)")
async def list_products(
    request: Request,
    write_db: Annotated[AsyncSession, Depends(get_write_db)],
    read_db: Annotated[AsyncSession, Depends(get_read_db)],
    fabric_ids: str | None = None,
    occasion_ids: str | None = None,
    region_ids: str | None = None,
    search: str | None = None,
    sort: SortOrder = SortOrder.NEWEST,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=48)] = 24,
) -> PagedProductListDTO:
    svc = _build_product_service(request, write_db, read_db)
    return await svc.list_products(
        fabric_ids=_parse_uuid_csv(fabric_ids),
        occasion_ids=_parse_uuid_csv(occasion_ids),
        region_ids=_parse_uuid_csv(region_ids),
        search=search,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/slug/{slug}",
    response_model=ProductDetailDTO,
    summary="Get product detail by slug",
)
async def get_product_by_slug(
    slug: str,
    request: Request,
    write_db: Annotated[AsyncSession, Depends(get_write_db)],
    read_db: Annotated[AsyncSession, Depends(get_read_db)],
) -> ProductDetailDTO:
    svc = _build_product_service(request, write_db, read_db)
    return await svc.get_product_by_slug(slug)


@router.get(
    "/{product_id}",
    response_model=ProductDetailDTO,
    summary="Get product detail by ID",
)
async def get_product(
    product_id: UUID,
    request: Request,
    write_db: Annotated[AsyncSession, Depends(get_write_db)],
    read_db: Annotated[AsyncSession, Depends(get_read_db)],
) -> ProductDetailDTO:
    svc = _build_product_service(request, write_db, read_db)
    return await svc.get_product_detail(product_id)


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=ProductDetailDTO,
    status_code=201,
    summary="Create a product (admin)",
)
async def create_product(
    body: CreateProductRequest,
    request: Request,
    write_db: Annotated[AsyncSession, Depends(get_write_db)],
    read_db: Annotated[AsyncSession, Depends(get_read_db)],
    _admin: Annotated[CurrentUser, Depends(require_admin)],
) -> ProductDetailDTO:
    svc = _build_product_service(request, write_db, read_db)
    return await svc.create_product(body)


@router.patch(
    "/{product_id}",
    response_model=ProductDetailDTO,
    summary="Partial update a product (admin)",
)
async def update_product(
    product_id: UUID,
    body: UpdateProductRequest,
    request: Request,
    write_db: Annotated[AsyncSession, Depends(get_write_db)],
    read_db: Annotated[AsyncSession, Depends(get_read_db)],
    _admin: Annotated[CurrentUser, Depends(require_admin)],
) -> ProductDetailDTO:
    svc = _build_product_service(request, write_db, read_db)
    return await svc.update_product(product_id, body)


@router.delete("/{product_id}", summary="Soft delete a product (admin)")
async def delete_product(
    product_id: UUID,
    request: Request,
    write_db: Annotated[AsyncSession, Depends(get_write_db)],
    read_db: Annotated[AsyncSession, Depends(get_read_db)],
    _admin: Annotated[CurrentUser, Depends(require_admin)],
) -> Response:
    svc = _build_product_service(request, write_db, read_db)
    await svc.soft_delete_product(product_id)
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Image endpoints (admin)
# ---------------------------------------------------------------------------


@router.post(
    "/{product_id}/images/presigned-url",
    response_model=PresignedUrlDTO,
    summary="Get S3 presigned upload URL (admin)",
)
async def get_presigned_upload_url(
    product_id: UUID,
    filename: str,
    content_type: str,
    request: Request,
    write_db: Annotated[AsyncSession, Depends(get_write_db)],
    read_db: Annotated[AsyncSession, Depends(get_read_db)],
    _admin: Annotated[CurrentUser, Depends(require_admin)],
) -> PresignedUrlDTO:
    svc = _build_product_service(request, write_db, read_db)
    return await svc.get_presigned_upload_url(product_id, filename, content_type)


@router.post(
    "/{product_id}/images/confirm",
    status_code=201,
    summary="Confirm image upload and create image record (admin)",
)
async def confirm_image_upload(
    product_id: UUID,
    body: ConfirmImageUploadRequest,
    request: Request,
    write_db: Annotated[AsyncSession, Depends(get_write_db)],
    read_db: Annotated[AsyncSession, Depends(get_read_db)],
    _admin: Annotated[CurrentUser, Depends(require_admin)],
) -> dict:  # type: ignore[type-arg]
    svc = _build_product_service(request, write_db, read_db)
    result = await svc.confirm_image_upload(product_id, body)
    return result.model_dump(mode="json")


@router.post(
    "/{product_id}/images/upload",
    status_code=201,
    summary="Upload image directly — local disk in dev, Cloudflare R2 in prod",
)
async def upload_image_local(
    product_id: UUID,
    file: Annotated[UploadFile, File(...)],
    request: Request,
    write_db: Annotated[AsyncSession, Depends(get_write_db)],
    read_db: Annotated[AsyncSession, Depends(get_read_db)],
    _admin: Annotated[CurrentUser, Depends(require_admin)],
) -> JSONResponse:
    """In development: save to uploads/local/ on disk and serve via StaticFiles.
    In production with R2 configured: upload directly to Cloudflare R2.
    """
    import io
    from application.dtos.product_dtos import ConfirmImageUploadRequest
    from infrastructure.persistence.models import ProductImageModel
    from sqlalchemy import select as _select

    env = os.environ.get("ENVIRONMENT", "development")
    r2_configured = bool(os.environ.get("R2_ACCOUNT_ID"))

    ext = os.path.splitext(file.filename or "image.jpg")[1] or ".jpg"
    filename = f"{_uuid.uuid4()}{ext}"
    s3_key = f"products/{product_id}/{filename}"
    contents = await file.read()

    if r2_configured and env != "development":
        # ── Production: upload to Cloudflare R2 ──────────────────────────────
        s3_adapter = request.app.state.service_factory._s3
        s3_adapter.upload_fileobj(
            io.BytesIO(contents), s3_key, file.content_type or "image/jpeg"
        )
    else:
        # ── Development: save to local disk ──────────────────────────────────
        subfolder = "local"
        uploads_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "uploads", subfolder, "products", str(product_id),
        )
        os.makedirs(uploads_dir, exist_ok=True)
        with open(os.path.join(uploads_dir, filename), "wb") as f:
            f.write(contents)

    svc = _build_product_service(request, write_db, read_db)
    existing = (await read_db.execute(
        _select(ProductImageModel).where(ProductImageModel.product_id == product_id)
    )).first()
    is_primary = existing is None
    result = await svc.confirm_image_upload(product_id, ConfirmImageUploadRequest(
        s3_key=s3_key, is_primary=is_primary, sort_order=0
    ))

    return JSONResponse(status_code=201, content={"url": result.cloudfront_url, "s3_key": s3_key})


@router.delete("/{product_id}/images/{image_id}", summary="Delete a product image (admin)")
async def delete_image(
    product_id: UUID,
    image_id: UUID,
    request: Request,
    write_db: Annotated[AsyncSession, Depends(get_write_db)],
    read_db: Annotated[AsyncSession, Depends(get_read_db)],
    _admin: Annotated[CurrentUser, Depends(require_admin)],
) -> Response:
    svc = _build_product_service(request, write_db, read_db)
    await svc.delete_image(product_id, image_id)
    return Response(status_code=204)
