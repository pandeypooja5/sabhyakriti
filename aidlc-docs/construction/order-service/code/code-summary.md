# Code Summary — Unit 4: Order Microservice

62 files generated under `sabhyakriti-order-service/`.

## Key Highlights
- OrderStatus: 10 states; only CONFIRMED→SHIPPED→DELIVERED admin-driven
- Shipping address denormalised as JSONB snapshot; no FK to addresses table
- Order number: SKB-{YYYYMM}-{SEQ:06d} via PostgreSQL sequence
- Stock reservation with compensating rollback if any item fails
- Partial returns: pro-rata discount + GST refund calculation with Decimal arithmetic
- 7-day return window from delivered_at timestamp
- Full GST invoice PDF via weasyprint + Jinja2 HTML template (HSN 5208, CGST+SGST)
- IDOR prevention on every customer order/address endpoint
- Fire-and-forget notification calls via asyncio.create_task
- Dual engine: primary for writes, replica for list/detail reads

## Tests
- Hypothesis PBT: 4 refund invariants (200 examples each)
- Parametrize: all 10 OrderStatus cancellability states, all valid/invalid status transitions, return window edge cases
- 12 application service tests: full lifecycle, compensating release, IDOR, COD vs paid cancel
- 8 address rule tests: max-5, auto-default, default promotion
