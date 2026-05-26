"""Customer address-book endpoints."""

from __future__ import annotations
from fastapi.responses import Response

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from application.dtos.order_dtos import (
    AddressDTO,
    CreateAddressRequest,
    UpdateAddressRequest,
)
from application.services.address_application_service import AddressApplicationService
from presentation.dependencies import (
    CurrentUser,
    get_address_service,
    get_current_user,
)

router = APIRouter(prefix="/api/v1/addresses", tags=["Addresses"])


@router.get("", response_model=list[AddressDTO])
async def list_addresses(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    address_svc: Annotated[AddressApplicationService, Depends(get_address_service)],
) -> list[AddressDTO]:
    """Return all saved addresses for the authenticated user."""
    return await address_svc.list_addresses(current_user.user_id)


@router.post("", response_model=AddressDTO, status_code=201)
async def add_address(
    body: CreateAddressRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    address_svc: Annotated[AddressApplicationService, Depends(get_address_service)],
) -> AddressDTO:
    """Add a new address (max 5 per user)."""
    return await address_svc.add_address(
        user_id=current_user.user_id,
        request=body,
    )


@router.patch("/{address_id}", response_model=AddressDTO)
async def update_address(
    address_id: UUID,
    body: UpdateAddressRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    address_svc: Annotated[AddressApplicationService, Depends(get_address_service)],
) -> AddressDTO:
    """Update a specific address (partial update supported)."""
    return await address_svc.update_address(
        address_id=address_id,
        user_id=current_user.user_id,
        request=body,
    )


@router.delete("/{address_id}")
async def delete_address(
    address_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    address_svc: Annotated[AddressApplicationService, Depends(get_address_service)],
) -> Response:
    """Delete an address; promotes next address to default if needed."""
    await address_svc.delete_address(
        address_id=address_id,
        user_id=current_user.user_id,
    )
    return Response(status_code=204)


@router.post("/{address_id}/set-default", response_model=AddressDTO)
async def set_default_address(
    address_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    address_svc: Annotated[AddressApplicationService, Depends(get_address_service)],
) -> AddressDTO:
    """Set an address as the default shipping address."""
    return await address_svc.set_default(
        address_id=address_id,
        user_id=current_user.user_id,
    )
