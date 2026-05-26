"""Cart REST API routes — authenticated user endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from application.dtos.cart_dtos import (
    AddToCartRequest,
    ApplyCouponRequest,
    CartDTO,
    UpdateQuantityRequest,
)
from application.services.cart_application_service import CartApplicationService
from presentation.dependencies import get_cart_service, get_current_user

router = APIRouter(prefix="/api/v1/cart", tags=["cart"])

CurrentUser = Annotated[dict, Depends(get_current_user)]
CartService = Annotated[CartApplicationService, Depends(get_cart_service)]


@router.get(
    "",
    response_model=CartDTO,
    summary="Get the current user's cart with live pricing",
)
async def get_cart(
    claims: CurrentUser,
    service: CartService,
) -> CartDTO:
    user_id = UUID(claims["sub"])
    return await service.get_cart(user_id)


@router.post(
    "/items",
    response_model=CartDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Add a product to the cart (increments if already present)",
)
async def add_item(
    body: AddToCartRequest,
    claims: CurrentUser,
    service: CartService,
) -> CartDTO:
    user_id = UUID(claims["sub"])
    return await service.add_item(user_id, body.product_id, body.quantity)


@router.patch(
    "/items/{cart_item_id}",
    response_model=CartDTO,
    summary="Update the quantity of a cart item (quantity=0 removes it)",
)
async def update_quantity(
    cart_item_id: UUID,
    body: UpdateQuantityRequest,
    claims: CurrentUser,
    service: CartService,
) -> CartDTO:
    user_id = UUID(claims["sub"])
    return await service.update_quantity(user_id, cart_item_id, body.quantity)


@router.delete(
    "/items/{cart_item_id}",
    response_model=CartDTO,
    summary="Remove a specific item from the cart",
)
async def remove_item(
    cart_item_id: UUID,
    claims: CurrentUser,
    service: CartService,
) -> CartDTO:
    user_id = UUID(claims["sub"])
    return await service.remove_item(user_id, cart_item_id)


@router.post(
    "/coupon",
    response_model=CartDTO,
    summary="Apply a coupon code to the cart",
)
async def apply_coupon(
    body: ApplyCouponRequest,
    claims: CurrentUser,
    service: CartService,
) -> CartDTO:
    user_id = UUID(claims["sub"])
    return await service.apply_coupon(user_id, body.coupon_code)


@router.delete(
    "/coupon",
    response_model=CartDTO,
    summary="Remove the applied coupon from the cart",
)
async def remove_coupon(
    claims: CurrentUser,
    service: CartService,
) -> CartDTO:
    user_id = UUID(claims["sub"])
    return await service.remove_coupon(user_id)
