# sabhyakriti-admin-service

Admin BFF (Backend-for-Frontend) for the Sabhyakriti platform. Pure aggregation — no database.

## Overview

This service aggregates data from all other microservices for the Admin Panel.
It owns no database schema; all data is fetched live on each request.

## Local Setup

```bash
cp .env.example .env   # fill in service URLs and secrets
docker-compose -f docker-compose.dev.yml up
```

Service runs at http://localhost:8007. Docs at http://localhost:8007/api/docs.

## Run Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/admin/dashboard | KPI dashboard (last 30 days) |
| GET | /api/v1/admin/reports/sales | Sales report (from/to date) |
| GET | /api/v1/admin/customers | List all customers |
| GET | /api/v1/admin/customers/{user_id} | Customer detail + order history |
| ALL | /api/v1/admin/products/* | Proxied to Product Service |
| ALL | /api/v1/admin/categories/* | Proxied to Product Service |
| ALL | /api/v1/admin/orders/* | Proxied to Order Service |
| ALL | /api/v1/admin/returns/* | Proxied to Order Service |
| ALL | /api/v1/admin/coupons/* | Proxied to Cart Service |
| GET | /health | Health check |

All endpoints require JWT with `role=ADMIN`.
