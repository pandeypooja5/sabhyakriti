# Business Rules — Unit 4: Order Microservice

---

## Order Creation Rules

| ID | Rule |
|---|---|
| BR-ORD-001 | Order is created from the current cart contents; cart is cleared after successful order creation |
| BR-ORD-002 | All cart item prices, names, and images are snapshotted into OrderItems at creation time |
| BR-ORD-003 | Shipping address is snapshotted as JSONB — changes to the address book do not affect existing orders |
| BR-ORD-004 | Stock is reserved via Product Service internal endpoint before order is persisted; if any item is out of stock → 409, order not created |
| BR-ORD-005 | For COD orders: initial status = CONFIRMED (no payment step needed) |
| BR-ORD-006 | For Razorpay/UPI orders: initial status = PENDING (awaits payment confirmation from Payment Service) |
| BR-ORD-007 | Order number format: `SKB-{YYYYMM}-{SEQ:06d}` (e.g., `SKB-202605-000001`); sequential per month using DB sequence |
| BR-ORD-008 | Order confirmation email + SMS sent after CONFIRMED status (via Notification Service) |

---

## Order Lifecycle Rules

| ID | Rule |
|---|---|
| BR-ORD-009 | Valid status transitions (admin-driven): CONFIRMED → SHIPPED → DELIVERED |
| BR-ORD-010 | Only admin can advance order status |
| BR-ORD-011 | `tracking_number` and `courier_name` must be provided when advancing to SHIPPED |
| BR-ORD-012 | `delivered_at` is set automatically when status is advanced to DELIVERED |
| BR-ORD-013 | `shipped_at` is set automatically when status is advanced to SHIPPED |
| BR-ORD-014 | Email + SMS notification sent on each status change |

---

## Cancellation Rules

| ID | Rule |
|---|---|
| BR-ORD-015 | Customer can cancel only if status is PENDING or CONFIRMED |
| BR-ORD-016 | Orders in SHIPPED, DELIVERED, or any return/refund status cannot be cancelled |
| BR-ORD-017 | On cancellation: set status = CANCELLED, `cancelled_at = NOW()` |
| BR-ORD-018 | Stock released via Product Service internal endpoint on cancellation |
| BR-ORD-019 | COD cancelled orders: no refund; notification sent |
| BR-ORD-020 | Razorpay/UPI CONFIRMED cancelled orders: Order Service calls Payment Service to initiate refund |
| BR-ORD-021 | PENDING cancelled orders (payment not yet captured): no refund needed; Payment Service cancels the pending payment |

---

## Return Request Rules

| ID | Rule |
|---|---|
| BR-ORD-022 | Return window = 7 days from `delivered_at` (Q1:A) |
| BR-ORD-023 | Return only allowed when order status = DELIVERED |
| BR-ORD-024 | Customer can make partial returns — select specific items and quantities (Q3:A) |
| BR-ORD-025 | Return quantity per item ≤ originally ordered quantity |
| BR-ORD-026 | Only one return request per order; if a return exists (any status), cannot create another |
| BR-ORD-027 | Reason is required (max 500 chars) |
| BR-ORD-028 | On return submission: set Order.status = RETURN_REQUESTED; create ReturnRequest (status=PENDING_REVIEW) |
| BR-ORD-029 | Admin approves return: set ReturnRequest.status = APPROVED; `refund_amount` calculated pro-rata |
| BR-ORD-030 | Admin rejects return: set ReturnRequest.status = REJECTED; Order.status → DELIVERED |
| BR-ORD-031 | After admin marks items received: ReturnRequest.status = ITEMS_RECEIVED |
| BR-ORD-032 | After admin initiates refund: status = REFUND_INITIATED; Order Service calls Payment Service refund API |
| BR-ORD-033 | After Payment Service confirms refund: status = REFUNDED; Order.status = REFUNDED |
| BR-ORD-034 | Refund amount for partial return = SUM(return_item.quantity × order_item.discounted_price); GST and discount pro-rated |
| BR-ORD-035 | Refund timeline communicated to customer: 3–5 business days (Q2:B) |
| BR-ORD-036 | COD orders that are returned: no online refund; store credit or manual bank transfer (out of scope for MVP — mark as REFUNDED after admin action) |

---

## Address Rules

| ID | Rule |
|---|---|
| BR-ORD-037 | Maximum 5 addresses per user |
| BR-ORD-038 | Exactly one default address per user (at most) |
| BR-ORD-039 | First address added automatically becomes default |
| BR-ORD-040 | Deleting default address: auto-promotes most recently created remaining address as default |
| BR-ORD-041 | PIN code validation: exactly 6 digits |

---

## Invoice Rules

| ID | Rule |
|---|---|
| BR-ORD-042 | Invoice type: Standard GST Invoice (Q4:A) |
| BR-ORD-043 | Invoice generated only for CONFIRMED, SHIPPED, DELIVERED, and RETURNED orders |
| BR-ORD-044 | Invoice number = Order.order_number |
| BR-ORD-045 | Invoice includes: seller GSTIN, seller address, buyer name + address, itemised list with HSN code `5208` (cotton woven fabric, covers sarees), taxable amount, GST (5%), total |
| BR-ORD-046 | Invoice generated as PDF using `reportlab` or `weasyprint` library |
| BR-ORD-047 | Invoice PDF served as download; not stored permanently in S3 (generated on demand) |
