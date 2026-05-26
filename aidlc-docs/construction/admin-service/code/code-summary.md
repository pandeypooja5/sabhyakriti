# Code Summary — Unit 7: Admin Microservice

~35 files generated under `sabhyakriti-admin-service/`.

## Architecture
- Pure BFF aggregation — **no database** (no SQLAlchemy, no Alembic, no asyncpg)
- All data fetched live via httpx from downstream services
- asyncio.gather with return_exceptions=True for all fan-out calls — partial failure safe

## Key Features
- Dashboard KPIs (last 30 days): revenue, orders, new customers, low-stock count, pending orders/returns, last 10 orders
- Sales report (view-only, max 365 days): revenue by day, top 10 products, category revenue, order status breakdown
- Customer management: list + detail with order history (parallel fetch)
- Proxy routes: all admin product/category/order/return/coupon endpoints pass-through to respective services with admin JWT
- Bulk CSV import proxied as multipart to Product Service

## Resilience
- If any downstream service fails, dashboard/report returns partial data with `service_unavailable: true`
- Customer detail: orders failure → empty orders list (user still returned)
- Customer detail: user failure → propagates error (user must exist)

## Tests
- 10 async unit tests covering: full success, single-service failure, all-services-down, date range validation, customer detail with order failure, customer-not-found propagation
