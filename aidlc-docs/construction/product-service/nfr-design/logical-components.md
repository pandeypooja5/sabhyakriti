# Logical Components — Unit 2: Product Microservice

---

## Component Map

```
HTTP Request
    |
    v
[SecurityHeadersMiddleware]
[RequestLoggingMiddleware]   ← structlog JSON
[JWTAuthMiddleware]          ← RS256 validation on admin/auth-required routes
[CORSMiddleware]
[GlobalExceptionHandler]
    |
    v
[FastAPI Routers]
    ProductRouter    /api/v1/products/*
    CategoryRouter   /api/v1/categories/*
    ReviewRouter     /api/v1/reviews/*
    MediaRouter      /api/v1/media/*
    InternalRouter   /internal/v1/products/*   (not via public ALB)
    HealthRouter     /health
    |
    v
[Application Services]
    ProductApplicationService
    CategoryApplicationService
    ReviewApplicationService
    |
    +---> [Cache Layer]
    |         PLPCacheRepository   ← Redis DB 1
    |
    +---> [Repository Interfaces]
    |         IProductRepository   (read + write sessions)
    |         ICategoryRepository
    |         IProductImageRepository
    |         IReviewRepository
    |
    +---> [External Clients]
              AWSS3Adapter         ← boto3 presigned URL generation
              AWSCloudFrontAdapter ← CDN URL construction
              OrderServiceClient  ← httpx, verified-purchase check
    |
    v
[Infrastructure]
    SQLAlchemy write engine  → RDS PRIMARY  (product schema)
    SQLAlchemy read engine   → RDS REPLICA  (product schema)
    Redis DB 1               → PLP cache
```

---

## Router Summary

| Router | Prefix | Auth | Key Routes |
|---|---|---|---|
| `ProductRouter` | `/api/v1/products` | None (list/detail); JWT+Admin (write) | GET / (list), GET /{id}, GET /slug/{slug}, POST / (admin), PATCH /{id} (admin), DELETE /{id} (admin), POST /{id}/images/presigned-url (admin), POST /{id}/images/confirm (admin), DELETE /{id}/images/{img_id} (admin) |
| `CategoryRouter` | `/api/v1/categories` | None (read); JWT+Admin (write) | GET / (all), GET /?type=FABRIC, POST / (admin), PATCH /{id} (admin), DELETE /{id} (admin) |
| `ReviewRouter` | `/api/v1/reviews` | JWT (submit/delete own) | GET /?product_id=, POST / (auth), DELETE /{id} (auth/admin) |
| `MediaRouter` | `/api/v1/media` | JWT+Admin | POST /presigned-url |
| `InternalRouter` | `/internal/v1/products` | Shared secret header | PATCH /{id}/stock (reserve/release), GET /verified-purchase (used by reviews) |
| `BulkUploadRouter` | `/api/v1/admin/products` | JWT+Admin | POST /bulk-import (CSV multipart) |
| `HealthRouter` | `/` | None | GET /health |

---

## Infrastructure Components

| Component | AWS Service | Config |
|---|---|---|
| Compute | EC2 t3.large | 1 instance, private subnet, Docker, port 8002 |
| Load balancer | ALB (shared) | Path `/api/v1/products/*`, `/api/v1/categories/*`, `/api/v1/reviews/*`, `/api/v1/media/*` → port 8002 |
| DB primary | RDS PostgreSQL 15 primary | `product` schema; writes |
| DB replica | RDS read replica | All customer reads |
| Cache | ElastiCache Redis DB 1 | PLP result cache; 5-min TTL |
| Image storage | AWS S3 | Bucket: `sabhyakriti-product-images`; block public access |
| Image CDN | AWS CloudFront | Origin: S3 bucket; domain: `cdn.sabhyakriti.com` |
| Logs | CloudWatch Logs | `/sabhyakriti/product-service`; 90-day retention |
| Container registry | ECR | `sabhyakriti/product-service` |
