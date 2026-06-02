"""
Order Application Service — orchestrates all order use-case flows.

Each public method corresponds to one business flow.  Application logic lives
here; domain rules live in domain/services/order_domain_service.py.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import structlog

from application.clients.notification_service_client import NotificationServiceClient
from application.clients.payment_service_client import PaymentServiceClient
from application.clients.product_service_client import ProductServiceClient
from application.dtos.order_dtos import (
    CancelOrderRequest,
    CartCheckoutDTO,
    ConfirmOrderRequest,
    CreateOrderRequest,
    OrderDTO,
    OrderItemDTO,
    OrderSummaryDTO,
    PagedOrderListDTO,
    ProcessReturnRequest,
    ReturnItemDTO,
    ReturnRequestDTO,
    SubmitReturnRequest,
    UpdateOrderStatusRequest,
)
from domain.entities.order import Order, OrderItem
from domain.entities.return_request import ReturnItem, ReturnRequest
from domain.repositories.i_order_repository import IOrderRepository
from domain.repositories.i_return_repository import IReturnRepository
from domain.services import order_domain_service as domain_svc
from domain.value_objects import (
    AddressSnapshot,
    OrderStatus,
    PaymentMethod,
    ReturnStatus,
)

logger = structlog.get_logger(__name__)


def _map_order_to_dto(order: Order) -> OrderDTO:
    from application.dtos.order_dtos import AddressSnapshotDTO

    items = [
        OrderItemDTO(
            order_item_id=item.order_item_id,
            product_id=item.product_id,
            variant_id=item.variant_id,
            product_name=item.product_name,
            product_image_url=item.product_image_url,
            unit_price=item.unit_price,
            discounted_price=item.discounted_price,
            quantity=item.quantity,
            hsn_code=item.hsn_code,
            cgst_rate=item.cgst_rate,
            sgst_rate=item.sgst_rate,
            line_total=item.line_total,
        )
        for item in order.items
    ]
    addr = AddressSnapshotDTO(**order.shipping_address.to_dict())
    return OrderDTO(
        order_id=order.order_id,
        user_id=order.user_id,
        order_number=order.order_number,
        status=order.status,
        payment_method=order.payment_method,
        payment_reference=order.payment_reference,
        shipping_address=addr,
        subtotal=order.subtotal,
        discount_amount=order.discount_amount,
        shipping_charge=order.shipping_charge,
        cgst_amount=order.cgst_amount,
        sgst_amount=order.sgst_amount,
        total_amount=order.total_amount,
        notes=order.notes,
        items=items,
        cancelled_at=order.cancelled_at,
        cancellation_reason=order.cancellation_reason,
        confirmed_at=order.confirmed_at,
        shipped_at=order.shipped_at,
        delivered_at=order.delivered_at,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


def _map_order_to_summary(order: Order) -> OrderSummaryDTO:
    return OrderSummaryDTO(
        order_id=order.order_id,
        order_number=order.order_number,
        status=order.status,
        payment_method=order.payment_method,
        total_amount=order.total_amount,
        item_count=len(order.items),
        created_at=order.created_at,
    )


def _map_return_to_dto(rr: ReturnRequest) -> ReturnRequestDTO:
    items = [
        ReturnItemDTO(
            return_item_id=ri.return_item_id,
            order_item_id=ri.order_item_id,
            quantity=ri.quantity,
            reason=ri.reason,
        )
        for ri in rr.items
    ]
    return ReturnRequestDTO(
        return_request_id=rr.return_request_id,
        order_id=rr.order_id,
        user_id=rr.user_id,
        status=rr.status,
        reason=rr.reason,
        items=items,
        refund_amount=rr.refund_amount,
        admin_notes=rr.admin_notes,
        processed_at=rr.processed_at,
        items_received_at=rr.items_received_at,
        refund_initiated_at=rr.refund_initiated_at,
        refunded_at=rr.refunded_at,
        created_at=rr.created_at,
        updated_at=rr.updated_at,
    )


class OrderApplicationService:
    """Orchestrates all order-related use cases."""

    def __init__(
        self,
        order_repo: IOrderRepository,
        return_repo: IReturnRepository,
        product_client: ProductServiceClient,
        payment_client: PaymentServiceClient,
        notification_client: NotificationServiceClient,
    ) -> None:
        self._order_repo = order_repo
        self._return_repo = return_repo
        self._product_client = product_client
        self._payment_client = payment_client
        self._notification_client = notification_client

    # ------------------------------------------------------------------
    # Flow 1: Create Order
    # ------------------------------------------------------------------

    async def create_order(
        self,
        user_id: str,
        address: object,  # Address domain entity
        request: CreateOrderRequest,
    ) -> OrderDTO:
        """
        Create a new order with stock reservation.

        - Reserves stock for each item; on any failure performs compensating
          releases for already-reserved items.
        - COD orders go directly to CONFIRMED; Razorpay/UPI start as PENDING.
        """
        from domain.entities.address import Address

        assert isinstance(address, Address)

        cart = request.cart_data
        payment_method = PaymentMethod(request.payment_method)

        # Build address snapshot
        address_snapshot = AddressSnapshot(
            address_id=str(address.address_id),
            full_name=address.full_name,
            phone=address.phone,
            address_line1=address.address_line1,
            address_line2=address.address_line2,
            city=address.city,
            state=address.state,
            pincode=address.pincode,
        )

        # Determine initial status
        initial_status = (
            OrderStatus.CONFIRMED
            if payment_method == PaymentMethod.COD
            else OrderStatus.PENDING
        )

        # Build order entity (order_number filled by repository via sequence)
        order_id = uuid.uuid4()
        now = datetime.now(tz=timezone.utc)

        order_items = [
            OrderItem(
                order_item_id=uuid.uuid4(),
                order_id=order_id,
                product_id=item.product_id,
                variant_id=item.variant_id,
                product_name=item.product_name,
                product_image_url=item.product_image_url,
                unit_price=item.unit_price,
                discounted_price=item.discounted_price,
                quantity=item.quantity,
                hsn_code=item.hsn_code,
            )
            for item in cart.items
        ]

        order = Order(
            order_id=order_id,
            user_id=user_id,
            order_number="",  # set by repository
            status=initial_status,
            payment_method=payment_method,
            payment_reference=None,
            shipping_address=address_snapshot,
            subtotal=cart.subtotal,
            discount_amount=cart.discount_amount,
            shipping_charge=cart.shipping_charge,
            cgst_amount=cart.cgst_amount,
            sgst_amount=cart.sgst_amount,
            total_amount=cart.total_amount,
            items=order_items,
            notes=request.notes,
            confirmed_at=now if initial_status == OrderStatus.CONFIRMED else None,
            created_at=now,
            updated_at=now,
        )

        # Reserve stock — compensating release on failure
        reserved: list[tuple[str, str | None, int]] = []
        try:
            for item in order_items:
                await self._product_client.reserve_stock(
                    item.product_id, item.variant_id, item.quantity
                )
                reserved.append((item.product_id, item.variant_id, item.quantity))
        except Exception as exc:
            logger.error("stock_reservation_failed", error=str(exc))
            for product_id, variant_id, qty in reserved:
                await self._product_client.release_stock(product_id, variant_id, qty)
            raise ValueError(
                "Stock reservation failed; order was not created."
            ) from exc

        saved_order = await self._order_repo.create(order)

        self._notification_client.notify_order_placed(
            user_id=user_id,
            order_id=str(saved_order.order_id),
            order_number=saved_order.order_number,
            total_amount=saved_order.total_amount,
        )

        if initial_status == OrderStatus.CONFIRMED:
            self._notification_client.notify_order_confirmed(
                user_id=user_id,
                order_id=str(saved_order.order_id),
                order_number=saved_order.order_number,
            )

        return _map_order_to_dto(saved_order)

    # ------------------------------------------------------------------
    # Flow 2: List Customer Orders
    # ------------------------------------------------------------------

    async def list_orders(
        self,
        user_id: str,
        page: int,
        page_size: int,
        status: str | None = None,
    ) -> PagedOrderListDTO:
        """Return paginated orders for the authenticated customer."""
        status_filter = OrderStatus(status) if status else None
        orders, total = await self._order_repo.list_by_user(
            user_id=user_id,
            page=page,
            page_size=page_size,
            status=status_filter,
        )
        total_pages = (total + page_size - 1) // page_size if total else 0
        return PagedOrderListDTO(
            items=[_map_order_to_summary(o) for o in orders],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    # ------------------------------------------------------------------
    # Flow 3: Get Order Detail
    # ------------------------------------------------------------------

    async def get_order(self, order_id: uuid.UUID, user_id: str) -> OrderDTO:
        """
        Fetch a single order.

        Raises PermissionError when the order belongs to a different user (IDOR).
        """
        order = await self._order_repo.get_by_id(order_id)
        if order is None:
            raise ValueError(f"Order {order_id} not found")
        if order.user_id != user_id:
            raise PermissionError("You do not have access to this order")
        return _map_order_to_dto(order)

    # ------------------------------------------------------------------
    # Flow 4: Cancel Order
    # ------------------------------------------------------------------

    async def cancel_order(
        self,
        order_id: uuid.UUID,
        user_id: str,
        request: CancelOrderRequest,
    ) -> OrderDTO:
        """
        Cancel a PENDING or CONFIRMED order.

        - Paid orders: calls Payment Service to initiate refund.
        - COD orders: no refund call.
        - Releases reserved stock for all items.
        """
        order = await self._order_repo.get_by_id_write(order_id)
        if order is None:
            raise ValueError(f"Order {order_id} not found")
        if order.user_id != user_id:
            raise PermissionError("You do not have access to this order")

        if not domain_svc.can_cancel(order):
            raise ValueError(
                f"Order cannot be cancelled in status '{order.status}'"
            )

        now = datetime.now(tz=timezone.utc)
        updated = await self._order_repo.update_status(
            order_id=order_id,
            new_status=OrderStatus.CANCELLED,
            cancelled_at=now,
            cancellation_reason=request.reason,
        )

        # Release stock for all items
        items = await self._order_repo.get_items(order_id)
        for item in items:
            await self._product_client.release_stock(
                item.product_id, item.variant_id, item.quantity
            )

        # Refund only for paid orders; never let a refund failure block the cancel
        if order.is_paid:
            try:
                await self._payment_client.initiate_refund(
                    order_id=str(order_id),
                    amount=order.total_amount,
                    reason="order_cancelled",
                )
            except Exception as exc:
                logger.error("refund_failed_during_cancel", order_id=str(order_id), error=str(exc))
        else:
            # PENDING/COD: cancel any pending payment record (no money to refund)
            try:
                await self._payment_client.cancel_pending_payment(str(order_id))
            except Exception:
                pass  # may not have a payment record

        self._notification_client.notify_order_cancelled(
            user_id=user_id,
            order_id=str(order_id),
            order_number=order.order_number,
            reason=request.reason,
        )

        return _map_order_to_dto(updated)

    # ------------------------------------------------------------------
    # Flow 5: Admin — List All Orders
    # ------------------------------------------------------------------

    async def admin_list_orders(
        self,
        page: int,
        page_size: int,
        status: str | None = None,
    ) -> PagedOrderListDTO:
        """Return paginated list of all orders (admin only)."""
        status_filter = OrderStatus(status) if status else None
        orders, total = await self._order_repo.list_all(
            page=page,
            page_size=page_size,
            status=status_filter,
        )
        total_pages = (total + page_size - 1) // page_size if total else 0
        return PagedOrderListDTO(
            items=[_map_order_to_summary(o) for o in orders],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def admin_list_orders_full(
        self,
        page: int,
        page_size: int,
        status: str | None = None,
    ) -> list[OrderDTO]:
        """Return paginated list of all orders as full DTOs (with shipping address)."""
        status_filter = OrderStatus(status) if status else None
        orders, _ = await self._order_repo.list_all(
            page=page,
            page_size=page_size,
            status=status_filter,
        )
        return [_map_order_to_dto(o) for o in orders]

    # ------------------------------------------------------------------
    # Flow 6: Admin — Update Order Status
    # ------------------------------------------------------------------

    async def update_order_status(
        self,
        order_id: uuid.UUID,
        request: UpdateOrderStatusRequest,
    ) -> OrderDTO:
        """
        Advance an order's status (CONFIRMED→SHIPPED, SHIPPED→DELIVERED).

        Validates the transition using domain rules.
        """
        order = await self._order_repo.get_by_id_write(order_id)
        if order is None:
            raise ValueError(f"Order {order_id} not found")

        new_status = OrderStatus(request.new_status)

        if not domain_svc.validate_status_transition(order.status, new_status):
            raise ValueError(
                f"Invalid status transition: {order.status} -> {new_status}"
            )

        now = datetime.now(tz=timezone.utc)
        extra: dict[str, object] = {}
        if new_status == OrderStatus.SHIPPED:
            extra["shipped_at"] = now
        elif new_status == OrderStatus.DELIVERED:
            extra["delivered_at"] = now

        updated = await self._order_repo.update_status(
            order_id=order_id,
            new_status=new_status,
            **extra,
        )

        if new_status == OrderStatus.SHIPPED:
            self._notification_client.notify_order_shipped(
                user_id=order.user_id,
                order_id=str(order_id),
                order_number=order.order_number,
            )
        elif new_status == OrderStatus.DELIVERED:
            self._notification_client.notify_order_delivered(
                user_id=order.user_id,
                order_id=str(order_id),
                order_number=order.order_number,
            )

        return _map_order_to_dto(updated)

    # ------------------------------------------------------------------
    # Flow 7: Confirm Order (internal — from Payment Service)
    # ------------------------------------------------------------------

    async def confirm_order(
        self,
        order_id: uuid.UUID,
        request: ConfirmOrderRequest,
    ) -> OrderDTO:
        """Mark a PENDING order as CONFIRMED after payment verification."""
        order = await self._order_repo.get_by_id_write(order_id)
        if order is None:
            raise ValueError(f"Order {order_id} not found")
        if order.status != OrderStatus.PENDING:
            raise ValueError(
                f"Order {order_id} is not in PENDING status (current: {order.status})"
            )

        now = datetime.now(tz=timezone.utc)
        updated = await self._order_repo.update_status(
            order_id=order_id,
            new_status=OrderStatus.CONFIRMED,
            confirmed_at=now,
            payment_reference=request.payment_reference,
        )

        self._notification_client.notify_order_confirmed(
            user_id=order.user_id,
            order_id=str(order_id),
            order_number=order.order_number,
        )

        return _map_order_to_dto(updated)

    # ------------------------------------------------------------------
    # Flow 8: Submit Return Request
    # ------------------------------------------------------------------

    async def submit_return(
        self,
        order_id: uuid.UUID,
        user_id: str,
        request: SubmitReturnRequest,
    ) -> ReturnRequestDTO:
        """
        Submit a return request for a delivered order within the return window.

        Supports partial returns — the customer can select specific items
        and quantities from the original order.
        """
        order = await self._order_repo.get_by_id(order_id)
        if order is None:
            raise ValueError(f"Order {order_id} not found")
        if order.user_id != user_id:
            raise PermissionError("You do not have access to this order")

        # Check for existing return
        existing = await self._return_repo.get_by_order_id(order_id)
        if existing is not None:
            raise ValueError("A return request already exists for this order")

        now = datetime.now(tz=timezone.utc)
        eligible, reason = domain_svc.can_request_return(order, now)
        if not eligible:
            raise ValueError(reason)

        # Build return items
        order_items = await self._order_repo.get_items(order_id)
        item_map = {str(oi.order_item_id): oi for oi in order_items}

        return_request_id = uuid.uuid4()
        return_items: list[ReturnItem] = []
        for ri_req in request.items:
            oi = item_map.get(str(ri_req.order_item_id))
            if oi is None:
                raise ValueError(
                    f"Order item {ri_req.order_item_id} not found in order"
                )
            if ri_req.quantity > oi.quantity:
                raise ValueError(
                    f"Return quantity {ri_req.quantity} exceeds ordered "
                    f"quantity {oi.quantity} for item {oi.product_name}"
                )
            return_items.append(
                ReturnItem(
                    return_item_id=uuid.uuid4(),
                    return_request_id=return_request_id,
                    order_item_id=ri_req.order_item_id,
                    quantity=ri_req.quantity,
                    reason=ri_req.reason,
                )
            )

        # Calculate refund amount
        return_domain_items = [
            ReturnItem(
                return_item_id=ri.return_item_id,
                return_request_id=return_request_id,
                order_item_id=ri.order_item_id,
                quantity=ri.quantity,
                reason=ri.reason,
            )
            for ri in return_items
        ]
        refund_amount = domain_svc.calculate_refund_amount(
            order, return_domain_items, order_items
        )

        return_request = ReturnRequest(
            return_request_id=return_request_id,
            order_id=order_id,
            user_id=user_id,
            status=ReturnStatus.PENDING_REVIEW,
            reason=request.reason,
            items=return_items,
            refund_amount=refund_amount,
            created_at=now,
            updated_at=now,
        )

        saved = await self._return_repo.create(return_request)

        # Update order status
        await self._order_repo.update_status(
            order_id=order_id,
            new_status=OrderStatus.RETURN_REQUESTED,
        )

        self._notification_client.notify_return_submitted(
            user_id=user_id,
            order_id=str(order_id),
            return_request_id=str(return_request_id),
        )

        return _map_return_to_dto(saved)

    # ------------------------------------------------------------------
    # Flow 9: Get Return Request
    # ------------------------------------------------------------------

    async def get_return(
        self,
        order_id: uuid.UUID,
        user_id: str,
    ) -> ReturnRequestDTO:
        """Get the return request for an order."""
        order = await self._order_repo.get_by_id(order_id)
        if order is None:
            raise ValueError(f"Order {order_id} not found")
        if order.user_id != user_id:
            raise PermissionError("You do not have access to this order")

        rr = await self._return_repo.get_by_order_id(order_id)
        if rr is None:
            raise ValueError(f"No return request found for order {order_id}")

        return _map_return_to_dto(rr)

    # ------------------------------------------------------------------
    # Flow 10: Admin — Process Return (Approve / Reject)
    # ------------------------------------------------------------------

    async def process_return(
        self,
        return_request_id: uuid.UUID,
        admin_user_id: str,
        request: ProcessReturnRequest,
    ) -> ReturnRequestDTO:
        """Approve or reject a pending return request."""
        rr = await self._return_repo.get_by_id(return_request_id)
        if rr is None:
            raise ValueError(f"Return request {return_request_id} not found")

        if rr.status != ReturnStatus.PENDING_REVIEW:
            raise ValueError(
                f"Return is not in PENDING_REVIEW status (current: {rr.status})"
            )

        now = datetime.now(tz=timezone.utc)

        if request.action == "APPROVE":
            new_return_status = ReturnStatus.APPROVED
            new_order_status = OrderStatus.RETURN_APPROVED
        else:
            new_return_status = ReturnStatus.REJECTED
            new_order_status = OrderStatus.RETURN_REJECTED

        updated_rr = await self._return_repo.update_status(
            return_request_id=return_request_id,
            new_status=new_return_status,
            admin_notes=request.admin_notes,
            processed_by=admin_user_id,
            processed_at=now,
        )

        await self._order_repo.update_status(
            order_id=rr.order_id,
            new_status=new_order_status,
        )

        if request.action == "APPROVE":
            self._notification_client.notify_return_approved(
                user_id=rr.user_id,
                order_id=str(rr.order_id),
                return_request_id=str(return_request_id),
            )
        else:
            self._notification_client.notify_return_rejected(
                user_id=rr.user_id,
                order_id=str(rr.order_id),
                return_request_id=str(return_request_id),
                admin_notes=request.admin_notes,
            )

        return _map_return_to_dto(updated_rr)

    # ------------------------------------------------------------------
    # Flow 11: Admin — Initiate Refund (mark received + call Payment)
    # ------------------------------------------------------------------

    async def initiate_return_refund(
        self,
        return_request_id: uuid.UUID,
        admin_user_id: str,
    ) -> ReturnRequestDTO:
        """
        Mark return items as received and initiate the refund via Payment Service.
        """
        rr = await self._return_repo.get_by_id(return_request_id)
        if rr is None:
            raise ValueError(f"Return request {return_request_id} not found")

        if rr.status != ReturnStatus.APPROVED:
            raise ValueError(
                f"Return must be APPROVED before refund (current: {rr.status})"
            )

        now = datetime.now(tz=timezone.utc)

        # Mark items received
        await self._return_repo.update_status(
            return_request_id=return_request_id,
            new_status=ReturnStatus.ITEMS_RECEIVED,
            items_received_at=now,
        )

        # Initiate refund
        await self._payment_client.initiate_refund(
            order_id=str(rr.order_id),
            amount=rr.refund_amount,
            reason="return_approved",
        )

        updated_rr = await self._return_repo.update_status(
            return_request_id=return_request_id,
            new_status=ReturnStatus.REFUND_INITIATED,
            refund_initiated_at=now,
        )

        await self._order_repo.update_status(
            order_id=rr.order_id,
            new_status=OrderStatus.REFUNDED,
        )

        self._notification_client.notify_refund_initiated(
            user_id=rr.user_id,
            order_id=str(rr.order_id),
            refund_amount=rr.refund_amount,
        )

        return _map_return_to_dto(updated_rr)

    # ------------------------------------------------------------------
    # Flow 12: Check Verified Purchase (internal — for Product Service)
    # ------------------------------------------------------------------

    async def check_verified_purchase(
        self, user_id: str, product_id: str
    ) -> bool:
        """Return True when the user has a delivered order containing product_id."""
        # list all delivered orders for this user and check for product
        orders, _ = await self._order_repo.list_by_user(
            user_id=user_id,
            page=1,
            page_size=100,
            status=OrderStatus.DELIVERED,
        )
        for order in orders:
            items = await self._order_repo.get_items(order.order_id)
            if any(i.product_id == product_id for i in items):
                return True
        return False
