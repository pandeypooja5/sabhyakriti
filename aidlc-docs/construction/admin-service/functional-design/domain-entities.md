# Functional Design — Unit 7: Admin Microservice

---

## Architecture: Pure Aggregation / BFF

Unit 7 owns **no database schema** and **no domain entities**.
All data is fetched via internal HTTP calls to other microservices.
The Admin Service is a Backend-for-Frontend (BFF) aggregation layer that:
1. Validates admin JWT on every request
2. Fans out calls to relevant services
3. Aggregates, computes, and shapes responses for the admin frontend

---

## Data Sources Per Feature

| Admin Feature | Source Services | Internal Endpoints Called |
|---|---|---|
| Dashboard KPIs | Order + Auth + Product | `/internal/v1/orders/stats`, `/internal/v1/users/stats`, `/internal/v1/products/low-stock` |
| Sales report (revenue by day) | Order | `/internal/v1/orders/stats?from=&to=&group_by=day` |
| Sales report (top products) | Order + Product | `/internal/v1/orders/top-products?from=&to=` → enrich with product names |
| Sales report (category) | Order + Product | `/internal/v1/orders/category-revenue?from=&to=` |
| Customer list | Auth | `/internal/v1/users?role=CUSTOMER&page=&page_size=` |
| Customer detail | Auth + Order | `/internal/v1/users/{id}` + `/internal/v1/orders/by-user/{user_id}` |
| All orders (admin) | Order | `/api/v1/admin/orders` (proxy) |
| Order status update | Order | `/api/v1/admin/orders/{id}/status` (proxy) |
| Return management | Order | `/api/v1/admin/returns/*` (proxy) |
| Product CRUD | Product | `/api/v1/products/*` (proxy with admin JWT) |
| Category CRUD | Product | `/api/v1/categories/*` (proxy) |
| Inventory update | Product | `/api/v1/products/{id}` PATCH stock_qty (proxy) |
| Coupon management | Cart | `/api/v1/admin/coupons/*` (proxy) |
| Bulk CSV import | Product | `/api/v1/admin/products/bulk-import` (proxy multipart) |

---

## Dashboard KPIs (last 30 days, Q1:B)

```
DashboardDTO:
  revenue_30d:          Decimal    — SUM(total_amount) of DELIVERED+SHIPPED orders, last 30 days
  orders_30d:           int        — COUNT of orders placed, last 30 days
  new_customers_30d:    int        — COUNT of users registered, last 30 days
  low_stock_products:   int        — COUNT of products WHERE stock_qty <= 5 AND is_active=True
  pending_orders:       int        — COUNT of orders WHERE status=CONFIRMED
  pending_returns:      int        — COUNT of return_requests WHERE status=PENDING_REVIEW
  recent_orders:        list[OrderSummaryDTO]  — last 10 orders (all statuses)
```

---

## Sales Report (view-only, Q2:A)

```
SalesReportDTO:
  from_date:            date
  to_date:              date
  total_revenue:        Decimal
  total_orders:         int
  revenue_by_day:       list[{date, revenue, order_count}]
  top_products:         list[{product_id, product_name, units_sold, revenue}]  — top 10
  category_revenue:     list[{category_name, category_type, revenue}]
  order_status_breakdown: dict[OrderStatus, int]
```

---

## Business Rules

| ID | Rule |
|---|---|
| BR-ADM-001 | All endpoints require JWT with role=ADMIN |
| BR-ADM-002 | Dashboard default period = last 30 rolling days |
| BR-ADM-003 | Sales report max date range = 365 days |
| BR-ADM-004 | Proxy endpoints pass the admin's JWT through to target services |
| BR-ADM-005 | If a downstream service is unavailable, return partial data with a `service_unavailable` flag |
| BR-ADM-006 | Admin service itself has no DB; all data fetched fresh on each request |
