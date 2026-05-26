"""Category API router."""
from __future__ import annotations
from fastapi.responses import Response

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from application.dtos.product_dtos import (
    CategoryDTO,
    CreateCategoryRequest,
    UpdateCategoryRequest,
)
from application.services.category_application_service import CategoryApplicationService
from domain.value_objects import CategoryType
from presentation.dependencies import CurrentUser, get_read_db, get_write_db, require_admin

router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


def _build_category_service(
    request: Request,
    write_session: AsyncSession,
    read_session: AsyncSession,
) -> CategoryApplicationService:
    return request.app.state.service_factory.build_category_service(
        write_session, read_session
    )


@router.get("", response_model=list[CategoryDTO], summary="List categories")
async def list_categories(
    request: Request,
    write_db: Annotated[AsyncSession, Depends(get_write_db)],
    read_db: Annotated[AsyncSession, Depends(get_read_db)],
    type: CategoryType | None = Query(default=None),
) -> list[CategoryDTO]:
    svc = _build_category_service(request, write_db, read_db)
    return await svc.list_categories(type=type)


@router.get("/{category_id}", response_model=CategoryDTO, summary="Get category by ID")
async def get_category(
    category_id: UUID,
    request: Request,
    write_db: Annotated[AsyncSession, Depends(get_write_db)],
    read_db: Annotated[AsyncSession, Depends(get_read_db)],
) -> CategoryDTO:
    svc = _build_category_service(request, write_db, read_db)
    return await svc.get_category(category_id)


@router.post(
    "",
    response_model=CategoryDTO,
    status_code=201,
    summary="Create a category (admin)",
)
async def create_category(
    body: CreateCategoryRequest,
    request: Request,
    write_db: Annotated[AsyncSession, Depends(get_write_db)],
    read_db: Annotated[AsyncSession, Depends(get_read_db)],
    _admin: Annotated[CurrentUser, Depends(require_admin)],
) -> CategoryDTO:
    svc = _build_category_service(request, write_db, read_db)
    return await svc.create_category(body)


@router.patch(
    "/{category_id}",
    response_model=CategoryDTO,
    summary="Update a category (admin)",
)
async def update_category(
    category_id: UUID,
    body: UpdateCategoryRequest,
    request: Request,
    write_db: Annotated[AsyncSession, Depends(get_write_db)],
    read_db: Annotated[AsyncSession, Depends(get_read_db)],
    _admin: Annotated[CurrentUser, Depends(require_admin)],
) -> CategoryDTO:
    svc = _build_category_service(request, write_db, read_db)
    return await svc.update_category(category_id, body)


@router.delete("/{category_id}", summary="Delete a category (admin)")
async def delete_category(
    category_id: UUID,
    request: Request,
    write_db: Annotated[AsyncSession, Depends(get_write_db)],
    read_db: Annotated[AsyncSession, Depends(get_read_db)],
    _admin: Annotated[CurrentUser, Depends(require_admin)],
) -> Response:
    svc = _build_category_service(request, write_db, read_db)
    await svc.delete_category(category_id)
    return Response(status_code=204)
