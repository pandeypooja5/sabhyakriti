"""Order and OrderItem domain entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from domain.value_objects import AddressSnapshot, OrderStatus, PaymentMethod


@dataclass
class OrderItem:
    """
    A single line item within an order.

    Snapshots product details at order creation time so the order history
    remains accurate even if the product catalogue is later changed.
    """

    order_item_id: UUID
    order_id: UUID
    product_id: str
    variant_id: str | None
    product_name: str
    product_image_url: str
    unit_price: Decimal
    discounted_price: Decimal
    quantity: int
    hsn_code: str = "5208"  # Cotton woven fabrics — standard for sarees
    cgst_rate: Decimal = Decimal("2.5")
    sgst_rate: Decimal = Decimal("2.5")
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def line_total(self) -> Decimal:
        """Total for this line at discounted price."""
        return self.discounted_price * self.quantity

    @property
    def tax_amount(self) -> Decimal:
        """Combined GST (CGST + SGST) on this line."""
        rate = (self.cgst_rate + self.sgst_rate) / Decimal("100")
        # Price is inclusive of GST; extract tax portion
        return (self.line_total * rate / (1 + rate)).quantize(Decimal("0.01"))


@dataclass
class Order:
    """Aggregate root representing a customer order."""

    order_id: UUID
    user_id: str
    order_number: str
    status: OrderStatus
    payment_method: PaymentMethod
    payment_reference: str | None
    shipping_address: AddressSnapshot
    subtotal: Decimal
    discount_amount: Decimal
    shipping_charge: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    total_amount: Decimal
    items: list[OrderItem] = field(default_factory=list)
    notes: str | None = None
    cancelled_at: datetime | None = None
    cancellation_reason: str | None = None
    confirmed_at: datetime | None = None
    shipped_at: datetime | None = None
    delivered_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def is_paid(self) -> bool:
        """True when payment method is not COD."""
        return self.payment_method != PaymentMethod.COD
