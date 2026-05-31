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


@router.get("", response_model=PagedProductListDTO, summary="List products (PLP)")
async def list_products(
    request: Request,
    write_db: Annotated[AsyncSession, Depends(get_write_db)],
    read_db: Annotated[AsyncSession, Depends(get_read_db)],
    fabric_ids: Annotated[list[UUID] | None, Query(alias="fabric_ids[]")] = None,
    occasion_ids: Annotated[list[UUID] | None, Query(alias="occasion_ids[]")] = None,
    region_ids: Annotated[list[UUID] | None, Query(alias="region_ids[]")] = None,
    search: str | None = None,
    sort: SortOrder = SortOrder.NEWEST,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=48)] = 24,
) -> PagedProductListDTO:
    svc = _build_product_service(request, write_db, read_db)
    return await svc.list_products(
        fabric_ids=fabric_ids,
        occasion_ids=occasion_ids,
        region_ids=region_ids,
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
    summary="Upload image file directly (local/dev — no S3 needed)",
)
async def upload_image_local(
    product_id: UUID,
    file: Annotated[UploadFile, File(...)],
    request: Request,
    write_db: Annotated[AsyncSession, Depends(get_write_db)],
    read_db: Annotated[AsyncSession, Depends(get_read_db)],
    _admin: Annotated[CurrentUser, Depends(require_admin)],
) -> JSONResponse:
    """Save image directly to uploads/local/{product_id}/ and register the record."""
    env = os.environ.get("ENVIRONMENT", "development")
    subfolder = "local" if env == "development" else "prod"

    # Save to uploads/{subfolder}/products/{product_id}/ so it's served at
    # /uploads/{subfolder}/products/{product_id}/{filename}
    # which matches build_cdn_url("products/{pid}/{file}", "host/uploads/{subfolder}")
    uploads_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "uploads", subfolder, "products", str(product_id),
    )
    os.makedirs(uploads_dir, exist_ok=True)

    ext = os.path.splitext(file.filename or "image.jpg")[1] or ".jpg"
    filename = f"{_uuid.uuid4()}{ext}"
    filepath = os.path.join(uploads_dir, filename)

    contents = await file.read()
    with open(filepath, "wb") as f:
        f.write(contents)

    # s3_key must have products/{product_id}/ prefix (validated by confirm_image_upload)
    s3_key = f"products/{product_id}/{filename}"

    # Register via service — build_cdn_url(s3_key, cloudfront_domain) produces the URL
    svc = _build_product_service(request, write_db, read_db)
    from application.dtos.product_dtos import ConfirmImageUploadRequest
    from infrastructure.persistence.models import ProductImageModel
    from sqlalchemy import select as _select
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
