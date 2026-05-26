"""Review API router."""
from __future__ import annotations
from fastapi.responses import Response

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from application.dtos.product_dtos import PagedReviewsDTO, ReviewDTO, SubmitReviewRequest
from application.services.review_application_service import ReviewApplicationService
from presentation.dependencies import (
    CurrentUser,
    get_current_user,
    get_read_db,
    get_write_db,
)

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])


def _build_review_service(
    request: Request,
    write_session: AsyncSession,
    read_session: AsyncSession,
) -> ReviewApplicationService:
    return request.app.state.service_factory.build_review_service(
        write_session, read_session
    )


@router.get("", response_model=PagedReviewsDTO, summary="List reviews for a product")
async def list_reviews(
    product_id: UUID,
    request: Request,
    write_db: Annotated[AsyncSession, Depends(get_write_db)],
    read_db: Annotated[AsyncSession, Depends(get_read_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 10,
) -> PagedReviewsDTO:
    svc = _build_review_service(request, write_db, read_db)
    return await svc.list_reviews(product_id, page=page, page_size=page_size)


@router.post("", response_model=ReviewDTO, status_code=201, summary="Submit a review")
async def submit_review(
    body: SubmitReviewRequest,
    request: Request,
    write_db: Annotated[AsyncSession, Depends(get_write_db)],
    read_db: Annotated[AsyncSession, Depends(get_read_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> ReviewDTO:
    svc = _build_review_service(request, write_db, read_db)
    return await svc.submit_review(current_user.user_id, body)


@router.delete("/{review_id}", summary="Delete a review (owner or admin)")
async def delete_review(
    review_id: UUID,
    request: Request,
    write_db: Annotated[AsyncSession, Depends(get_write_db)],
    read_db: Annotated[AsyncSession, Depends(get_read_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> Response:
    svc = _build_review_service(request, write_db, read_db)
    is_admin = current_user.role == "ADMIN"
    await svc.delete_review(
        review_id,
        requesting_user_id=current_user.user_id,
        is_admin=is_admin,
    )
    return Response(status_code=204)
