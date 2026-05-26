"""Cart Application Service — orchestrates all cart business flows.

Flows implemented:
  1.  get_cart           — fetch cart with live prices and totals
  2.  add_item           — add or increment product in cart
  3.  update_quantity    — set exact quantity (0 = remove)
  4.  remove_item        — delete item from cart
  5.  apply_coupon       — validate and attach coupon
  6.  remove_coupon      — detach coupon
  7.  get_wishlist       — fetch wishlist with live prices
  8.  add_to_wishlist    — add product to wishlist
  9.  remove_from_wishlist — remove product from wishlist
  10. get_cart_for_checkout — internal: validate stock + return checkout payload
  11. clear_cart         — internal: clear all items + coupon
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from application.clients.product_service_client import (
    ProductPriceDTO,
    ProductServiceClient,
)
from application.dtos.cart_dtos import (
    CartCheckoutDTO,
    CartDTO,
    CartItemDTO,
    CartTotalsDTO,
    CheckoutItemDTO,
    WishlistDTO,
    WishlistItemDTO,
)
from domain.entities.coupon import Coupon
from domain.repositories.i_cart_repository import ICartRepository
from domain.repositories.i_coupon_repository import ICouponRepository
from domain.repositories.i_wishlist_repository import IWishlistRepository
from domain.services.pricing_service import CartItemWithPrice, calculate_totals

logger = logging.getLogger(__name__)


class CartApplicationService:
    """Orchestrates all cart, wishlist, and checkout flows."""

    def __init__(
        self,
        cart_repo: ICartRepository,
        wishlist_repo: IWishlistRepository,
        coupon_repo: ICouponRepository,
        product_client: ProductServiceClient,
    ) -> None:
        self._cart_repo = cart_repo
        self._wishlist_repo = wishlist_repo
        self._coupon_repo = coupon_repo
        self._product_client = product_client

    # ------------------------------------------------------------------
    # Flow 1: Get cart with live prices
    # ------------------------------------------------------------------

    async def get_cart(self, user_id: UUID) -> CartDTO:
        """Return the user's cart with live pricing from Product Service."""
        cart = await self._cart_repo.get_or_create(user_id)
        items = await self._cart_repo.get_items(cart.cart_id)

        if not items:
            totals = calculate_totals([], None, price_stale=False)
            return CartDTO(
                cart_id=cart.cart_id,
                items=[],
                totals=_totals_to_dto(totals),
                item_count=0,
            )

        product_ids = [item.product_id for item in items]
        product_map, price_stale = await self._fetch_prices(product_ids)

        coupon = await self._load_coupon(cart.applied_coupon_code)
        priced_items = _build_priced_items(items, product_map)
        totals = calculate_totals(priced_items, coupon, price_stale=price_stale)

        item_dtos = _build_item_dtos(items, product_map, price_stale)
        return CartDTO(
            cart_id=cart.cart_id,
            items=item_dtos,
            totals=_totals_to_dto(totals),
            item_count=len(items),
        )

    # ------------------------------------------------------------------
    # Flow 2: Add item to cart
    # ------------------------------------------------------------------

    async def add_item(
        self,
        user_id: UUID,
        product_id: UUID,
        quantity: int,
    ) -> CartDTO:
        """Add a product to the cart or increment quantity.

        Raises:
            ValueError: if max 20 products or max qty 10 per item exceeded
        """
        cart = await self._cart_repo.get_or_create(user_id)
        await self._cart_repo.add_item(cart.cart_id, product_id, quantity)
        return await self.get_cart(user_id)

    # ------------------------------------------------------------------
    # Flow 3: Update item quantity
    # ------------------------------------------------------------------

    async def update_quantity(
        self,
        user_id: UUID,
        cart_item_id: UUID,
        quantity: int,
    ) -> CartDTO:
        """Set exact quantity for a cart item. quantity=0 removes the item.

        Raises:
            LookupError: if cart item not found
            ValueError: if quantity exceeds 10
        """
        cart = await self._cart_repo.get_or_create(user_id)

        if quantity == 0:
            removed = await self._cart_repo.remove_item(cart_item_id, cart.cart_id)
            if not removed:
                raise LookupError(f"Cart item {cart_item_id} not found.")
        else:
            updated = await self._cart_repo.update_item_quantity(
                cart_item_id, cart.cart_id, quantity
            )
            if updated is None:
                raise LookupError(f"Cart item {cart_item_id} not found.")

        return await self.get_cart(user_id)

    # ------------------------------------------------------------------
    # Flow 4: Remove item
    # ------------------------------------------------------------------

    async def remove_item(self, user_id: UUID, cart_item_id: UUID) -> CartDTO:
        """Remove an item from the cart.

        Raises:
            LookupError: if item not found
        """
        cart = await self._cart_repo.get_or_create(user_id)
        removed = await self._cart_repo.remove_item(cart_item_id, cart.cart_id)
        if not removed:
            raise LookupError(f"Cart item {cart_item_id} not found.")
        return await self.get_cart(user_id)

    # ------------------------------------------------------------------
    # Flow 5: Apply coupon
    # ------------------------------------------------------------------

    async def apply_coupon(self, user_id: UUID, coupon_code: str) -> CartDTO:
        """Apply a coupon to the cart.

        Raises:
            LookupError: if coupon not found
            ValueError:  if coupon is invalid for the current cart state
        """
        cart = await self._cart_repo.get_or_create(user_id)
        coupon = await self._coupon_repo.find_by_code(coupon_code)
        if coupon is None:
            raise LookupError(f"Coupon '{coupon_code}' not found.")

        # Compute current subtotal with live prices
        items = await self._cart_repo.get_items(cart.cart_id)
        product_ids = [item.product_id for item in items]
        product_map, _ = await self._fetch_prices(product_ids)
        priced_items = _build_priced_items(items, product_map)

        from domain.services.pricing_service import calculate_subtotal

        subtotal = calculate_subtotal(priced_items)

        now = datetime.now(tz=timezone.utc)
        valid, error = coupon.is_valid(now, subtotal)
        if not valid:
            raise ValueError(error)

        await self._cart_repo.apply_coupon(cart.cart_id, coupon.code)
        return await self.get_cart(user_id)

    # ------------------------------------------------------------------
    # Flow 6: Remove coupon
    # ------------------------------------------------------------------

    async def remove_coupon(self, user_id: UUID) -> CartDTO:
        """Remove the applied coupon from the cart."""
        cart = await self._cart_repo.get_or_create(user_id)
        await self._cart_repo.remove_coupon(cart.cart_id)
        return await self.get_cart(user_id)

    # ------------------------------------------------------------------
    # Flow 7: Get wishlist with live prices
    # ------------------------------------------------------------------

    async def get_wishlist(self, user_id: UUID) -> WishlistDTO:
        """Return the user's wishlist with live pricing."""
        wishlist = await self._wishlist_repo.get_or_create(user_id)
        items = await self._wishlist_repo.get_items(wishlist.wishlist_id)

        if not items:
            return WishlistDTO(wishlist_id=wishlist.wishlist_id, items=[])

        product_ids = [item.product_id for item in items]
        product_map, _ = await self._fetch_prices(product_ids)

        item_dtos = [
            WishlistItemDTO(
                wishlist_item_id=item.wishlist_item_id,
                product_id=item.product_id,
                product_name=product_map[item.product_id].name
                if item.product_id in product_map
                else "Unknown Product",
                primary_image_url=product_map[item.product_id].primary_image_url
                if item.product_id in product_map
                else None,
                discounted_price=product_map[item.product_id].discounted_price
                if item.product_id in product_map
                else Decimal("0"),
                stock_status=product_map[item.product_id].stock_status
                if item.product_id in product_map
                else "UNKNOWN",
                is_available=product_map[item.product_id].is_active
                and product_map[item.product_id].stock_status != "OUT_OF_STOCK"
                if item.product_id in product_map
                else False,
            )
            for item in items
        ]

        return WishlistDTO(wishlist_id=wishlist.wishlist_id, items=item_dtos)

    # ------------------------------------------------------------------
    # Flow 8: Add to wishlist
    # ------------------------------------------------------------------

    async def add_to_wishlist(
        self, user_id: UUID, product_id: UUID
    ) -> WishlistDTO:
        """Add a product to the wishlist (idempotent)."""
        wishlist = await self._wishlist_repo.get_or_create(user_id)
        await self._wishlist_repo.add_item(wishlist.wishlist_id, product_id)
        return await self.get_wishlist(user_id)

    # ------------------------------------------------------------------
    # Flow 9: Remove from wishlist
    # ------------------------------------------------------------------

    async def remove_from_wishlist(
        self, user_id: UUID, product_id: UUID
    ) -> WishlistDTO:
        """Remove a product from the wishlist.

        Raises:
            LookupError: if item not found
        """
        wishlist = await self._wishlist_repo.get_or_create(user_id)
        removed = await self._wishlist_repo.remove_item(
            wishlist.wishlist_id, product_id
        )
        if not removed:
            raise LookupError(f"Product {product_id} not in wishlist.")
        return await self.get_wishlist(user_id)

    # ------------------------------------------------------------------
    # Flow 10: Internal — get cart for checkout (validates stock)
    # ------------------------------------------------------------------

    async def get_cart_for_checkout(self, user_id: UUID) -> CartCheckoutDTO:
        """Return cart data for Order Service checkout.

        Raises:
            LookupError: if cart is empty
            PermissionError: if any item has stock_qty=0 (returns 409 via handler)
        """
        cart = await self._cart_repo.get_or_create(user_id)
        items = await self._cart_repo.get_items(cart.cart_id)

        if not items:
            raise LookupError("Cart is empty.")

        product_ids = [item.product_id for item in items]
        product_map, price_stale = await self._fetch_prices(product_ids)

        # Validate stock for all items
        out_of_stock = [
            item.product_id
            for item in items
            if item.product_id in product_map
            and product_map[item.product_id].stock_status == "OUT_OF_STOCK"
        ]
        if out_of_stock:
            raise ValueError(
                f"Items out of stock: {[str(pid) for pid in out_of_stock]}"
            )

        coupon = await self._load_coupon(cart.applied_coupon_code)
        priced_items = _build_priced_items(items, product_map)
        totals = calculate_totals(priced_items, coupon, price_stale=price_stale)

        checkout_items = [
            CheckoutItemDTO(
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=product_map[item.product_id].discounted_price
                if item.product_id in product_map
                else Decimal("0"),
                item_total=(
                    product_map[item.product_id].discounted_price * item.quantity
                )
                if item.product_id in product_map
                else Decimal("0"),
            )
            for item in items
        ]

        return CartCheckoutDTO(
            cart_id=cart.cart_id,
            user_id=user_id,
            items=checkout_items,
            totals=_totals_to_dto(totals),
            coupon_code=cart.applied_coupon_code,
        )

    # ------------------------------------------------------------------
    # Flow 11: Internal — clear cart
    # ------------------------------------------------------------------

    async def clear_cart(self, user_id: UUID) -> None:
        """Delete all items and clear coupon (idempotent).

        Called by Order Service after successful order placement.
        """
        cart = await self._cart_repo.get_by_user_id(user_id)
        if cart is None:
            return  # Idempotent — nothing to clear
        await self._cart_repo.clear_cart(cart.cart_id)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _fetch_prices(
        self, product_ids: list[UUID]
    ) -> tuple[dict[UUID, ProductPriceDTO], bool]:
        """Fetch live prices. Returns (product_map, price_stale)."""
        product_map = await self._product_client.get_products_batch(product_ids)
        price_stale = len(product_map) == 0 and len(product_ids) > 0
        return product_map, price_stale

    async def _load_coupon(self, coupon_code: str | None) -> Coupon | None:
        if coupon_code is None:
            return None
        return await self._coupon_repo.find_by_code(coupon_code)


# ---------------------------------------------------------------------------
# Module-level pure helpers
# ---------------------------------------------------------------------------

def _build_priced_items(
    items: list,
    product_map: dict[UUID, ProductPriceDTO],
) -> list[CartItemWithPrice]:
    return [
        CartItemWithPrice(
            product_id=item.product_id,
            quantity=item.quantity,
            discounted_price=product_map[item.product_id].discounted_price
            if item.product_id in product_map
            else Decimal("0"),
        )
        for item in items
    ]


def _build_item_dtos(
    items: list,
    product_map: dict[UUID, ProductPriceDTO],
    price_stale: bool,
) -> list[CartItemDTO]:
    dtos = []
    for item in items:
        info = product_map.get(item.product_id)
        price = info.discounted_price if info else Decimal("0")
        dtos.append(
            CartItemDTO(
                cart_item_id=item.cart_item_id,
                product_id=item.product_id,
                product_name=info.name if info else "Unknown Product",
                primary_image_url=info.primary_image_url if info else None,
                discounted_price=price,
                quantity=item.quantity,
                item_total=price * item.quantity,
                stock_status=info.stock_status if info else "UNKNOWN",
                is_available=bool(info and info.is_active and info.stock_status != "OUT_OF_STOCK"),
                price_stale=price_stale,
            )
        )
    return dtos


def _totals_to_dto(totals: object) -> CartTotalsDTO:
    from domain.value_objects import CartTotals

    assert isinstance(totals, CartTotals)
    return CartTotalsDTO(
        subtotal=totals.subtotal,
        discount_amount=totals.discount_amount,
        gst_amount=totals.gst_amount,
        shipping_charge=totals.shipping_charge,
        total=totals.total,
        coupon_code=totals.coupon_code,
        price_stale=totals.price_stale,
    )
