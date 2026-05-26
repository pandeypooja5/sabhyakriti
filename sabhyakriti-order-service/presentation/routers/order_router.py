"""Customer-facing order endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from application.dtos.order_dtos import (
    CancelOrderRequest,
    CreateOrderRequest,
    OrderDTO,
    PagedOrderListDTO,
    ReturnRequestDTO,
    SubmitReturnRequest,
)
from application.services.invoice_service import InvoiceService
from application.services.order_application_service import OrderApplicationService
from presentation.dependencies import (
    CurrentUser,
    get_address_service,
    get_current_user,
    get_invoice_service,
    get_order_service,
)
from application.services.address_application_service import AddressApplicationService

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


@router.post("", response_model=OrderDTO, status_code=201)
async def create_order(
    body: CreateOrderRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    order_svc: Annotated[OrderApplicationService, Depends(get_order_service)],
    address_svc: Annotated[AddressApplicationService, Depends(get_address_service)],
) -> OrderDTO:
    """Place a new order from the customer's cart."""
    address = await address_svc.get_by_id(body.address_id, current_user.user_id)
    return await order_svc.create_order(
        user_id=current_user.user_id,
        address=address,
        request=body,
    )


@router.get("", response_model=PagedOrderListDTO)
async def list_orders(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    order_svc: Annotated[OrderApplicationService, Depends(get_order_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None),
) -> PagedOrderListDTO:
    """List orders for the authenticated customer."""
    return await order_svc.list_orders(
        user_id=current_user.user_id,
        page=page,
        page_size=page_size,
        status=status,
    )


@router.get("/{order_id}", response_model=OrderDTO)
async def get_order(
    order_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    order_svc: Annotated[OrderApplicationService, Depends(get_order_service)],
) -> OrderDTO:
    """Get full detail of a single order (IDOR-protected)."""
    return await order_svc.get_order(order_id=order_id, user_id=current_user.user_id)


@router.post("/{order_id}/cancel", response_model=OrderDTO)
async def cancel_order(
    order_id: UUID,
    body: CancelOrderRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    order_svc: Annotated[OrderApplicationService, Depends(get_order_service)],
) -> OrderDTO:
    """Cancel a PENDING or CONFIRMED order."""
    return await order_svc.cancel_order(
        order_id=order_id,
        user_id=current_user.user_id,
        request=body,
    )


@router.get("/{order_id}/invoice")
async def download_invoice(
    order_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    order_svc: Annotated[OrderApplicationService, Depends(get_order_service)],
    invoice_svc: Annotated[InvoiceService, Depends(get_invoice_service)],
) -> StreamingResponse:
    """Download the PDF invoice for an order."""
    order_dto = await order_svc.get_order(
        order_id=order_id, user_id=current_user.user_id
    )
    pdf_bytes = await invoice_svc.generate_invoice_pdf(order_dto)

    filename = f"invoice-{order_dto.order_number}.pdf"
    return StreamingResponse(
        content=iter([pdf_bytes]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )


@router.post("/{order_id}/returns", response_model=ReturnRequestDTO, status_code=201)
async def submit_return(
    order_id: UUID,
    body: SubmitReturnRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    order_svc: Annotated[OrderApplicationService, Depends(get_order_service)],
) -> ReturnRequestDTO:
    """Submit a return request for a delivered order."""
    return await order_svc.submit_return(
        order_id=order_id,
        user_id=current_user.user_id,
        request=body,
    )


@router.get("/{order_id}/returns", response_model=ReturnRequestDTO)
async def get_return(
    order_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    order_svc: Annotated[OrderApplicationService, Depends(get_order_service)],
) -> ReturnRequestDTO:
    """Get the return request associated with an order."""
    return await order_svc.get_return(
        order_id=order_id,
        user_id=current_user.user_id,
    )
