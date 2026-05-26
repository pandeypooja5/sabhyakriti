# Business Logic Model — Unit 4: Order Microservice

---

## Flow 1: Create Order

```
Input: user_id, address_id, payment_method

1. Load cart from Cart Service (GET /internal/v1/cart/{user_id})
   → 404 if no cart or cart empty
   → 409 if any items out of stock (Cart Service validates)
2. Load address by address_id; verify belongs to user → 404 if not
3. Reserve stock: for each cart item, call Product Service
   PATCH /internal/v1/products/{id}/stock {delta: +quantity}
   → If any fails with 409: release already-reserved stock (compensating calls), return 409
4. Generate order_number (DB sequence: SKB-{YYYYMM}-{SEQ:06d})
5. Snapshot shipping_address as JSONB
6. Calculate totals from cart data (subtotal, discount, GST, shipping=0, total)
7. Create Order {status=PENDING if Razorpay/UPI, CONFIRMED if COD}
8. Create OrderItems (snapshot product_name, product_image_url, unit_price, discounted_price)
9. Clear cart: DELETE /internal/v1/cart/{user_id}
10. IF COD: trigger NotificationService.send_order_confirmation (async)
    IF Razorpay/UPI: return order_id to Payment Service to initiate payment
11. Return OrderDTO
```

---

## Flow 2: Confirm Order (called by Payment Service after payment captured)

```
Input: order_id, payment_id (internal call)

1. Load order → 404 if not found
2. Validate status = PENDING → 409 if already CONFIRMED/CANCELLED
3. Update Order.status = CONFIRMED, Order.confirmed_at = NOW()
4. Trigger NotificationService.send_order_confirmation (async)
5. Return OrderDTO
```

---

## Flow 3: Get Order Detail (Customer)

```
Input: user_id, order_id

1. Load order → 404 if not found
2. Validate order.user_id = user_id → 403 if mismatch (IDOR prevention)
3. Load OrderItems
4. Load ReturnRequest if exists
5. Return OrderDTO { order, items, return_request? }
```

---

## Flow 4: List Orders (Customer)

```
Input: user_id, page, page_size (default 10)

1. SELECT orders WHERE user_id = ? ORDER BY placed_at DESC
2. LIMIT/OFFSET pagination
3. Return PagedOrderListDTO (summary: order_number, status, total, placed_at, item_count)
```

---

## Flow 5: Cancel Order (Customer)

```
Input: user_id, order_id, reason (optional)

1. Load order → 404 if not found; verify user_id → 403 if mismatch
2. Check status IN (PENDING, CONFIRMED) → 400 "Order cannot be cancelled at this stage" if not
3. Update Order.status = CANCELLED, cancelled_at = NOW()
4. Release stock: for each OrderItem, call Product Service
   PATCH /internal/v1/products/{id}/stock {delta: -quantity} (negative = release)
5. IF payment_method != COD AND status was CONFIRMED:
   Call Payment Service /internal/v1/payments/{order_id}/refund (async)
6. Trigger NotificationService.send_order_cancelled (async)
7. Return OrderDTO
```

---

## Flow 6: Update Order Status (Admin)

```
Input: admin_id, order_id, new_status, tracking_number?, courier_name?

1. Load order → 404
2. Validate transition: CONFIRMED→SHIPPED or SHIPPED→DELIVERED only
3. IF new_status = SHIPPED:
   → tracking_number required → 400 if missing
   → Update: status=SHIPPED, tracking_number, courier_name, shipped_at=NOW()
4. IF new_status = DELIVERED:
   → Update: status=DELIVERED, delivered_at=NOW()
5. Trigger relevant notification (async):
   SHIPPED → NotificationService.send_order_shipped(tracking_number)
   DELIVERED → NotificationService.send_order_delivered
6. Return OrderDTO
```

---

## Flow 7: Submit Return Request (Customer)

```
Input: user_id, order_id, reason, items: [{order_item_id, quantity, reason?}]

1. Load order → verify user_id (IDOR) → 404/403
2. Validate status = DELIVERED → 400 "Order must be delivered before returning"
3. Validate 7-day window: NOW() ≤ delivered_at + 7 days → 400 "Return window has closed"
4. Check no existing ReturnRequest for this order → 409 "A return request already exists"
5. Validate each return item:
   a. order_item_id belongs to this order → 400 if not
   b. return quantity ≤ order item quantity → 400 if exceeded
6. Calculate refund_amount:
   returnable_total = SUM(item.quantity × item.discounted_price)
   refund_fraction = returnable_total / order.subtotal
   refund_amount = ROUND(returnable_total - (order.discount_amount × refund_fraction) +
                         (order.gst_amount × refund_fraction), 2)
7. Create ReturnRequest {status=PENDING_REVIEW, refund_amount}
8. Create ReturnItems
9. Update Order.status = RETURN_REQUESTED
10. Trigger NotificationService.send_return_received (async)
11. Return ReturnRequestDTO
```

---

## Flow 8: Process Return Request (Admin)

```
Input: admin_id, return_id, action (APPROVE/REJECT), admin_notes?

1. Load ReturnRequest → 404; validate status = PENDING_REVIEW
2. IF action = REJECT:
   Update ReturnRequest.status = REJECTED
   Update Order.status = DELIVERED (revert to delivered)
   Trigger notification (return rejected)
3. IF action = APPROVE:
   Update ReturnRequest.status = APPROVED
   Update Order.status = RETURN_APPROVED
   Trigger notification (return approved, instruct customer to ship items back)
4. Return ReturnRequestDTO
```

---

## Flow 9: Mark Items Received + Initiate Refund (Admin)

```
Input: admin_id, return_id

1. Load ReturnRequest; validate status = APPROVED
2. Update ReturnRequest.status = ITEMS_RECEIVED → then REFUND_INITIATED
3. Release returned stock: for each ReturnItem, call Product Service
   PATCH /internal/v1/products/{id}/stock {delta: -quantity}
4. Call Payment Service /internal/v1/payments/{order_id}/refund {amount: refund_amount}
5. Update Order.status = REFUNDED; ReturnRequest.status = REFUNDED
6. Trigger NotificationService.send_refund_processed(amount=refund_amount)
7. Return ReturnRequestDTO
```

---

## Flow 10: Generate Invoice PDF

```
Input: user_id, order_id

1. Load order → verify user_id (IDOR)
2. Validate status IN (CONFIRMED, SHIPPED, DELIVERED, RETURNED, REFUNDED) → 400 if PENDING/CANCELLED
3. Load OrderItems
4. Build invoice data:
   - Seller: Sabhyakriti, GSTIN, address
   - Buyer: shipping_address snapshot
   - Items: product_name, HSN 5208, quantity, unit_price, discounted_price, item_total
   - Tax: GST 5% (shown as SGST 2.5% + CGST 2.5% for intra-state or IGST 5% for inter-state)
   - Totals: subtotal, discount, taxable amount, GST, total
5. Render PDF using weasyprint (HTML template → PDF)
6. Return StreamingResponse (application/pdf, filename=invoice_{order_number}.pdf)
```

---

## Flow 11: Address Management

```
Create:  validate pincode (6 digits), max 5 addresses; if first → set is_default=True
Update:  partial update; if is_default=True → clear existing default first
Delete:  if deleting default → promote next most-recent as default
Set default: clear existing default, set new default
List:    return all addresses for user (no pagination — max 5)
```

---

## Flow 12: Internal — Verified Purchase Check (Product Service → Order Service)

```
Input: user_id, product_id (internal call, shared secret)

1. SELECT 1 FROM orders o
   JOIN order_items oi ON oi.order_id = o.order_id
   WHERE o.user_id = user_id AND oi.product_id = product_id AND o.status = 'DELIVERED'
   LIMIT 1
2. Return { verified: true/false }
```

---

## Error Response Standards

| Scenario | HTTP | Message |
|---|---|---|
| Order not found | 404 | "Order not found." |
| IDOR attempt | 403 | "You do not have access to this order." |
| Cannot cancel | 400 | "Order cannot be cancelled at this stage." |
| Return window closed | 400 | "Return window has closed (7 days from delivery)." |
| Duplicate return | 409 | "A return request already exists for this order." |
| Insufficient stock at create | 409 | "Some items are out of stock: {names}" |
| Invalid status transition | 400 | "Invalid status transition from {current} to {new}." |
| Address limit | 400 | "Maximum 5 addresses allowed." |
