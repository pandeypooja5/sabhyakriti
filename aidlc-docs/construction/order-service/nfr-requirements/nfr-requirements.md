# NFR Requirements — Unit 4: Order Microservice

## Performance
| ID | Requirement | Target |
|---|---|---|
| NFR-ORD-PERF-01 | Create order p95 (includes stock reserve + cart clear) | < 1.5s |
| NFR-ORD-PERF-02 | Get order detail p95 | < 300ms |
| NFR-ORD-PERF-03 | List orders p95 | < 400ms |
| NFR-ORD-PERF-04 | Invoice PDF generation p95 | < 2s |
| NFR-ORD-PERF-05 | All other endpoints p95 | < 500ms |

## Scalability
- EC2 t3.medium (order writes are less frequent than reads)
- DB pool: pool_size=3, max_overflow=7
- Read replica used for list_orders and get_order_detail queries

## Availability
- 99.9% uptime
- Stock reservation uses DB transaction + compensating releases on failure
- Notification Service calls are fire-and-forget (async background tasks)
- Payment Service refund calls are async; order status updated via webhook

## Security
- All 15 SECURITY rules enforced
- IDOR prevention: every order access verifies `order.user_id == current_user.user_id`
- Internal endpoints (`/internal/v1/*`) require shared-secret header
- Address pincode validated (6 digits) at input
- No payment data stored — only `payment_method` enum value

## Testing
- 80% line coverage
- PBT (Hypothesis): refund amount calculation (partial return fractions), GST pro-rating
- Integration tests for full order lifecycle (create → confirm → ship → deliver → return → refund)

## PDF Invoice Library
- `weasyprint` for HTML→PDF rendering (CSS-styled GST invoice template)
