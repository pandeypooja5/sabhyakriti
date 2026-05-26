"""Coupon admin REST API routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from application.dtos.cart_dtos import (
    CouponDTO,
    CreateCouponRequest,
    UpdateCouponRequest,
)
from application.services.coupon_application_service import CouponApplicationService
from presentation.dependencies import get_coupon_service, require_admin

router = APIRouter(prefix="/api/v1/admin/coupons", tags=["admin-coupons"])

AdminUser = Annotated[dict, Depends(require_admin)]
CouponService = Annotated[CouponApplicationService, Depends(get_coupon_service)]


@router.get(
    "",
    response_model=list[CouponDTO],
    summary="List all coupons (admin only)",
)
async def list_coupons(
    _claims: AdminUser,
    service: CouponService,
) -> list[CouponDTO]:
    return await service.list_coupons()


@router.post(
    "",
    response_model=CouponDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new coupon (admin only)",
)
async def create_coupon(
    body: CreateCouponRequest,
    _claims: AdminUser,
    service: CouponService,
) -> CouponDTO:
    return await service.create_coupon(body)


@router.patch(
    "/{coupon_id}",
    response_model=CouponDTO,
    summary="Update a coupon (admin only)",
)
async def update_coupon(
    coupon_id: UUID,
    body: UpdateCouponRequest,
    _claims: AdminUser,
    service: CouponService,
) -> CouponDTO:
    return await service.update_coupon(coupon_id, body)


@router.delete(
    "/{coupon_id}",
    response_model=CouponDTO,
    summary="Deactivate a coupon (admin only)",
)
async def deactivate_coupon(
    coupon_id: UUID,
    _claims: AdminUser,
    service: CouponService,
) -> CouponDTO:
    return await service.deactivate_coupon(coupon_id)
