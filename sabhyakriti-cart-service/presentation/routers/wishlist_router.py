"""Wishlist REST API routes — authenticated user endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from application.dtos.cart_dtos import AddToWishlistRequest, WishlistDTO
from application.services.cart_application_service import CartApplicationService
from presentation.dependencies import get_cart_service, get_current_user

router = APIRouter(prefix="/api/v1/wishlist", tags=["wishlist"])

CurrentUser = Annotated[dict, Depends(get_current_user)]
CartService = Annotated[CartApplicationService, Depends(get_cart_service)]


@router.get(
    "",
    response_model=WishlistDTO,
    summary="Get the current user's wishlist with live product info",
)
async def get_wishlist(
    claims: CurrentUser,
    service: CartService,
) -> WishlistDTO:
    user_id = UUID(claims["sub"])
    return await service.get_wishlist(user_id)


@router.post(
    "/items",
    response_model=WishlistDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Add a product to the wishlist (idempotent)",
)
async def add_to_wishlist(
    body: AddToWishlistRequest,
    claims: CurrentUser,
    service: CartService,
) -> WishlistDTO:
    user_id = UUID(claims["sub"])
    return await service.add_to_wishlist(user_id, body.product_id)


@router.delete(
    "/items/{product_id}",
    response_model=WishlistDTO,
    summary="Remove a product from the wishlist",
)
async def remove_from_wishlist(
    product_id: UUID,
    claims: CurrentUser,
    service: CartService,
) -> WishlistDTO:
    user_id = UUID(claims["sub"])
    return await service.remove_from_wishlist(user_id, product_id)
