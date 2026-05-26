# Code Generation Plan — Unit 2: Product Microservice
# sabhyakriti-product-service

---

## Unit Context

| Field | Value |
|---|---|
| Repository | `sabhyakriti-product-service` |
| Code location | `C:\AI-Projects\sabhyakriti\sabhyakriti-product-service\` |
| Port | 8002 |
| Requirements | FR-PLP-01–13, FR-PDP-01–15, FR-ADM-03–06, FR-ADM-12 |
| Depends on | Unit 1 JWT public key (for auth validation), Order Service client (for review verified-purchase) |

---

## Generation Steps

### Step 1: Project Structure
- [x] 1.1 `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`
- [x] 1.2 `.env.example`, `Dockerfile`, `docker-compose.dev.yml`
- [x] 1.3 `.github/workflows/product-service.yml`
- [x] 1.4 Full directory tree

### Step 2: Domain Layer — Entities & Value Objects
- [x] 2.1 `domain/entities/product.py` — Product, ProductImage dataclasses with `stock_status`, `discounted_price` computed properties
- [x] 2.2 `domain/entities/category.py` — Category dataclass
- [x] 2.3 `domain/entities/review.py` — Review dataclass
- [x] 2.4 `domain/value_objects.py` — CategoryType, StockStatus, SortOrder, Money
- [x] 2.5 `domain/services/pricing_service.py` — `discounted_price`, `savings_amount`, `stock_status` logic
- [x] 2.6 `domain/services/slug_service.py` — slugify, collision-safe slug generation
- [x] 2.7 Repository interfaces: `i_product_repository.py`, `i_category_repository.py`, `i_image_repository.py`, `i_review_repository.py`

### Step 3: Domain Tests
- [x] 3.1 `tests/domain/test_pricing_service.py` — PBT with Hypothesis: discount_percentage boundaries, rounding
- [x] 3.2 `tests/domain/test_slug_service.py` — PBT: unicode input, special chars, long names, collision
- [x] 3.3 `tests/domain/test_stock_status.py` — parametrize all StockStatus thresholds

### Step 4: Application Layer
- [x] 4.1 `application/dtos/product_dtos.py` — all request/response Pydantic v2 schemas (ProductSummaryDTO, ProductDetailDTO, PagedProductListDTO, ReviewDTO, CategoryDTO, PresignedUrlDTO, BulkImportResultDTO, …)
- [x] 4.2 `application/services/product_application_service.py` — Flows 1–5, 8–10 from business-logic-model.md
- [x] 4.3 `application/services/review_application_service.py` — Flows 6–7
- [x] 4.4 `application/services/category_application_service.py` — category CRUD
- [x] 4.5 `application/clients/order_service_client.py` — async httpx client for verified-purchase check (fail-open)

### Step 5: Application Tests
- [x] 5.1 `tests/application/test_product_service_list.py` — filter combinations, search, sort, pagination
- [x] 5.2 `tests/application/test_product_service_admin.py` — create, update, slug generation, image upload flow, bulk CSV
- [x] 5.3 `tests/application/test_review_service.py` — verified purchase, duplicate review, rating update
- [x] 5.4 `tests/application/test_category_service.py` — CRUD, delete guard

### Step 6: Infrastructure — DB + Cache
- [x] 6.1 `infrastructure/persistence/database.py` — dual engine (primary + replica)
- [x] 6.2 `infrastructure/persistence/models.py` — all 4 ORM models in `product` schema with FTS trigger DDL
- [x] 6.3 `infrastructure/persistence/repositories/sqlalchemy_product_repository.py` — list (filter/search/sort/paginate), get_by_id, get_by_slug, create, update, soft_delete, reserve_stock, release_stock
- [x] 6.4 `infrastructure/persistence/repositories/sqlalchemy_category_repository.py`
- [x] 6.5 `infrastructure/persistence/repositories/sqlalchemy_image_repository.py`
- [x] 6.6 `infrastructure/persistence/repositories/sqlalchemy_review_repository.py`
- [x] 6.7 `infrastructure/cache/plp_cache_repository.py` — Redis cache-aside; invalidate_all()
- [x] 6.8 `alembic/versions/0001_create_product_schema.py` — schema + tables + indexes + FTS trigger

### Step 7: Infrastructure Tests
- [x] 7.1 `tests/infrastructure/test_sqlalchemy_product_repository.py` — filter combos, FTS, pagination (real PostgreSQL)
- [x] 7.2 `tests/infrastructure/test_plp_cache_repository.py` — cache hit, miss, invalidation (fakeredis)

### Step 8: Adapters
- [x] 8.1 `infrastructure/adapters/aws_s3_adapter.py` — `generate_presigned_put_url(s3_key, ttl, content_type)`, `delete_object(s3_key)`
- [x] 8.2 `infrastructure/adapters/aws_cloudfront_adapter.py` — `build_cdn_url(s3_key)` → `https://cdn.sabhyakriti.com/{s3_key}`

### Step 9: Adapter Tests
- [x] 9.1 `tests/infrastructure/test_s3_adapter.py` — mock boto3; presigned URL generation; content-type validation

### Step 10: Presentation Layer
- [x] 10.1 All middleware (reuse patterns from Unit 1)
- [x] 10.2 `presentation/routers/product_router.py` — all public + admin product endpoints
- [x] 10.3 `presentation/routers/category_router.py`
- [x] 10.4 `presentation/routers/review_router.py`
- [x] 10.5 `presentation/routers/media_router.py`
- [x] 10.6 `presentation/routers/internal_router.py` — stock reserve/release (shared secret auth)
- [x] 10.7 `presentation/routers/bulk_upload_router.py` — CSV multipart upload
- [x] 10.8 `presentation/routers/health_router.py`
- [x] 10.9 `presentation/dependencies.py`
- [x] 10.10 `main.py`

### Step 11: Integration Tests
- [x] 11.1 `tests/integration/test_plp_filter_flow.py` — multi-filter combos, search + filter, pagination
- [x] 11.2 `tests/integration/test_product_admin_flow.py` — create → upload image → confirm → activate
- [x] 11.3 `tests/integration/test_review_flow.py` — submit review, duplicate rejection, delete

### Step 12: Documentation
- [x] 12.1 `aidlc-docs/construction/product-service/code/code-summary.md`
- [x] 12.2 `README.md`

---

## Story Traceability

| Req ID | Step |
|---|---|
| FR-PLP-01–13 | 4.2, 6.3, 10.2 |
| FR-PDP-01–15 | 4.2, 6.3, 10.2 |
| FR-ADM-03–05 | 4.2, 4.4, 10.2, 10.3 |
| FR-ADM-06 | 4.2, 6.3 (stock update) |
| FR-ADM-12 | 4.2, 8.1, 10.5 |

## Total: 12 steps, 48 sub-tasks
