# Business Logic Model — Unit 3: Cart & Wishlist Microservice

---

## Flow 1: Get Cart with Live Totals

```
Input: user_id (from JWT)

1. Load Cart for user → if none, return empty CartDTO { items: [], totals: zeroed }
2. Load all CartItems for this cart
3. IF cart has items:
   a. Fetch live product details from Product Service:
      GET /api/v1/products?ids=[product_id1, product_id2, ...]  (batch endpoint)
      → on timeout/failure: use last-known prices with price_stale=True flag (BR-CART-027)
   b. For each CartItem: attach product name, primary_image_url, discounted_price, stock_status
      → if product_id not found in response: mark item is_available=False (product deleted/deactivated)
4. Load applied coupon details (if applied_coupon_code is set)
5. Calculate CartTotals:
   subtotal        = SUM(item.quantity × item.discounted_price) for available items
   discount_amount = apply_coupon(subtotal, coupon)  [0 if no coupon]
   taxable_amount  = subtotal - discount_amount
   gst_amount      = ROUND(taxable_amount × 0.05, 2)
   shipping_charge = 0.00
   total           = taxable_amount + gst_amount
6. Return CartDTO { items: [CartItemDTO], totals: CartTotalsDTO, coupon_applied }
```

---

## Flow 2: Add Item to Cart

```
Input: user_id, product_id, quantity (1–10)

1. Validate quantity (BR-CART-033)
2. Load or create Cart for user
3. Verify product exists and is active:
   GET /api/v1/products/{product_id} from Product Service
   → 404 if product not found or is_active=False
4. Check cart item count:
   IF distinct product count ≥ 20 AND product_id not already in cart → HTTP 400 (BR-CART-005)
5. Upsert CartItem (BR-CART-003):
   IF CartItem for this (cart_id, product_id) exists:
     new_qty = existing_qty + quantity
     IF new_qty > 10 → HTTP 400 (BR-CART-006)
     UPDATE CartItem.quantity = new_qty
   ELSE:
     INSERT CartItem { cart_id, product_id, quantity }
6. UPDATE Cart.updated_at = NOW()
7. Return updated CartDTO (recalculate totals per Flow 1)
```

---

## Flow 3: Update Cart Item Quantity

```
Input: user_id, cart_item_id, quantity (0–10)

1. Load CartItem → 404 if not found; verify it belongs to user's cart
2. IF quantity = 0: delete CartItem (BR-CART-007) → return updated cart
3. IF quantity > 10: HTTP 400 (BR-CART-006)
4. UPDATE CartItem.quantity = quantity
5. UPDATE Cart.updated_at = NOW()
6. Return updated CartDTO
```

---

## Flow 4: Remove Item from Cart

```
Input: user_id, cart_item_id

1. Load CartItem → 404 if not found; verify it belongs to user's cart
2. DELETE CartItem
3. UPDATE Cart.updated_at = NOW()
4. Return updated CartDTO
```

---

## Flow 5: Apply Coupon

```
Input: user_id, coupon_code

1. Load Cart for user → 404 if no cart
2. Normalise coupon_code to UPPERCASE
3. Load Coupon by code → 404 "Coupon not found or invalid" if missing
4. Validate coupon (BR-CART-012 to BR-CART-015):
   a. is_active = TRUE → else 400 "This coupon is no longer active"
   b. expires_at IS NULL OR expires_at > NOW() → else 400 "This coupon has expired"
   c. max_uses IS NULL OR used_count < max_uses → else 400 "This coupon has reached its usage limit"
   d. Calculate current subtotal; check ≥ min_order_amount → else 400 "Minimum order ₹{min} required for this coupon"
5. UPDATE Cart.applied_coupon_code = coupon_code
6. Return updated CartDTO with recalculated totals
```

---

## Flow 6: Remove Coupon

```
Input: user_id

1. Load Cart → 404 if no cart
2. UPDATE Cart.applied_coupon_code = NULL
3. Return updated CartDTO
```

---

## Flow 7: Get Wishlist

```
Input: user_id

1. Load Wishlist → if none, return empty WishlistDTO
2. Load all WishlistItems
3. Batch-fetch product details from Product Service
4. Return WishlistDTO { items: [WishlistItemDTO { product_id, product_name, primary_image_url,
   discounted_price, stock_status, is_available }] }
```

---

## Flow 8: Add to Wishlist

```
Input: user_id, product_id

1. Load or create Wishlist for user
2. UPSERT WishlistItem (idempotent — BR-CART-029):
   INSERT INTO wishlist_items ... ON CONFLICT (wishlist_id, product_id) DO NOTHING
3. Return 200 { message: "Added to wishlist" }
```

---

## Flow 9: Remove from Wishlist

```
Input: user_id, product_id

1. Load Wishlist → 404 if no wishlist
2. DELETE WishlistItem WHERE (wishlist_id, product_id) → 404 if not found
3. Return 200 { message: "Removed from wishlist" }
```

---

## Flow 10: Internal — Read Cart for Order (Order Service)

```
Input: user_id (internal shared-secret auth)

1. Load Cart + CartItems + applied coupon for user
2. Fetch live product prices from Product Service
3. Validate all items are available (stock > 0)
   → If any item is_available=False: return 409 { unavailable_items: [...] }
4. Return CartCheckoutDTO {
     cart_id, user_id,
     items: [{ product_id, quantity, unit_price, subtotal }],
     totals: CartTotalsDTO,
     coupon_code
   }
```

---

## Flow 11: Internal — Clear Cart (Order Service)

```
Input: user_id (internal shared-secret auth)

1. Load Cart → no-op if no cart (idempotent)
2. DELETE all CartItems WHERE cart_id = ?
3. UPDATE Cart.applied_coupon_code = NULL, updated_at = NOW()
4. Return 204
```

---

## Flow 12: Admin — Manage Coupons (CRUD)

```
Create:  validate code unique, type, value range, dates → INSERT Coupon
Update:  partial update (deactivate, change expiry, adjust max_uses)
List:    paginated with filters (active/expired/type)
Delete:  soft-delete (is_active = FALSE); hard delete not supported
```

---

## Error Response Standards

| Scenario | HTTP | Message |
|---|---|---|
| Cart item limit | 400 | "Cart can contain at most 20 different products." |
| Quantity limit | 400 | "Maximum quantity per item is 10." |
| Coupon not found | 404 | "Coupon not found or invalid." |
| Coupon expired | 400 | "This coupon has expired." |
| Coupon inactive | 400 | "This coupon is no longer active." |
| Coupon max uses | 400 | "This coupon has reached its usage limit." |
| Coupon min order | 400 | "Minimum order amount of ₹{min} required for this coupon." |
| Unavailable items at checkout | 409 | "Some items are out of stock: {product names}" |
