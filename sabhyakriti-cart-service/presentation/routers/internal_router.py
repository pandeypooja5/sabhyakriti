"""Internal REST API routes — service-to-service, shared-secret protected.

Used exclusively by Order Service. Not exposed to external traffic.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from application.dtos.cart_dtos import CartCheckoutDTO
from application.services.cart_application_service import CartApplicationService
from presentation.dependencies import get_cart_service, verify_internal_secret

router = APIRouter(
    prefix="/internal/v1/cart",
    tags=["internal"],
    dependencies=[Depends(verify_internal_secret)],
)

CartService = Annotated[CartApplicationService, Depends(get_cart_service)]


@router.get(
    "/{user_id}",
    response_model=CartCheckoutDTO,
    summary="Read cart for checkout (Order Service) — validates stock",
    responses={
        409: {"description": "One or more items are out of stock"},
    },
)
async def get_cart_for_checkout(
    user_id: UUID,
    service: CartService,
    response: Response,
) -> CartCheckoutDTO:
    """Return the full cart payload for Order Service checkout.

    Returns 409 if any item has stock_qty=0.
    """
    try:
        return await service.get_cart_for_checkout(user_id)
    except ValueError as exc:
        response.status_code = status.HTTP_409_CONFLICT
        from fastapi.responses import JSONResponse

        return JSONResponse(  # type: ignore[return-value]
            status_code=409,
            content={"detail": str(exc)},
        )


@router.delete(
    "/{user_id}",
    summary="Clear cart after order placed (Order Service) — idempotent",
)
async def clear_cart(
    user_id: UUID,
    service: CartService,
) -> Response:
    """Delete all items and clear coupon from the user's cart.

    Idempotent — safe to call even if cart is already empty.
    """
    await service.clear_cart(user_id)
    return Response(status_code=204)
