# Code Summary — Unit 2: Product Microservice

All files generated under `sabhyakriti-product-service/`. 71 files total.

## Project Setup
- `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `.env.example`
- `Dockerfile` — python:3.11-slim, non-root, 4 Uvicorn workers, port 8002
- `docker-compose.dev.yml` — PostgreSQL 15 + Redis 7 for local dev
- `alembic.ini`

## Domain Layer
- `domain/value_objects.py` — CategoryType, StockStatus, SortOrder, Money
- `domain/entities/product.py` — Product + ProductImage dataclasses; computed `discounted_price`, `stock_status`, `savings_amount` properties
- `domain/entities/category.py`, `review.py`
- `domain/services/pricing_service.py` — `calculate_discounted_price`, `calculate_stock_status`, `calculate_savings`
- `domain/services/slug_service.py` — python-slugify + collision-safe UUID-8 suffix
- Repository interfaces: `i_product_repository.py`, `i_category_repository.py`, `i_image_repository.py`, `i_review_repository.py`, `i_plp_cache_repository.py`

## Application Layer
- `application/dtos/product_dtos.py` — ProductSummaryDTO, ProductDetailDTO, PagedProductListDTO, ReviewDTO, CategoryDTO, PresignedUrlDTO, BulkImportResultDTO + all request schemas
- `application/services/product_application_service.py` — all 11 flows: PLP list (cache-aside), PDP detail, presigned URL, confirm upload, delete image, create/update/soft-delete product, bulk CSV import, reserve/release stock
- `application/services/review_application_service.py` — list, submit (verified purchase check + fail-open), delete + rating recalculation
- `application/services/category_application_service.py` — CRUD with delete guard
- `application/clients/order_service_client.py` — httpx async; 2s timeout; 1 retry; None on unreachable (fail-open)

## Infrastructure — Persistence
- `infrastructure/persistence/database.py` — dual async engines: primary (writes) + read replica (reads)
- `infrastructure/persistence/models.py` — ProductModel, CategoryModel, ProductCategoryModel, ProductImageModel, ReviewModel in `product` schema; TSVECTOR column type
- `infrastructure/persistence/repositories/sqlalchemy_product_repository.py` — dynamic filter query (within-dim OR via subquery, cross-dim AND); tsvector search; 5 sort modes; reserve_stock with row-level lock
- `infrastructure/persistence/repositories/sqlalchemy_category_repository.py`
- `infrastructure/persistence/repositories/sqlalchemy_image_repository.py` — auto-promotes primary on delete
- `infrastructure/persistence/repositories/sqlalchemy_review_repository.py` — `recalculate_product_stats` updates denormalised fields
- `infrastructure/cache/plp_cache_repository.py` — Redis cache-aside; `invalidate_all` scans and deletes `product_plp:*`
- `alembic/versions/0001_create_product_schema.py` — full schema + tables + indexes + GIN index + FTS trigger

## Infrastructure — Adapters
- `infrastructure/adapters/aws_s3_adapter.py` — presigned PUT URL (15-min TTL), delete object, content-type validation
- `infrastructure/adapters/aws_cloudfront_adapter.py` — `build_cdn_url`
- `infrastructure/adapters/aws_secrets_adapter.py` — Secrets Manager loader

## Presentation Layer
- Middleware: SecurityHeaders, RequestLogging, GlobalExceptionHandler
- `presentation/dependencies.py` — get_read_db, get_write_db, get_redis, get_current_user (RS256 JWT), require_admin, verify_internal_secret
- Routers: product_router (9 routes), category_router, review_router, internal_router (stock + verified-purchase), bulk_upload_router (CSV multipart), health_router
- `main.py` — dual engine + Redis + service wiring via lifespan

## Tests
- `tests/domain/` — Hypothesis PBT: pricing formula (discount boundaries), slug (unicode/special chars/collisions), stock status thresholds
- `tests/application/` — PLP cache hit/miss/invalidation; review flows (verified/unverified/unreachable/duplicate)
- `tests/infrastructure/` — fakeredis: cache set/get, TTL, invalidate_all
