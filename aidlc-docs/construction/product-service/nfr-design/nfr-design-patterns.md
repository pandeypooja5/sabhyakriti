# NFR Design Patterns — Unit 2: Product Microservice

---

## 1. PLP Result Cache Pattern (Redis Cache-Aside)

**Pattern**: Cache-Aside with TTL-based invalidation
**Application**: All `list_products` results

```
Request arrives:
  1. Compute cache_key = SHA-256(json({fabric_ids, occasion_ids, region_ids, search, sort, page, page_size}))
  2. GET Redis key product_plp:{cache_key}
     HIT  → deserialise + return (p95 < 300ms)
     MISS → execute DB query → serialise → SET Redis key product_plp:{cache_key} EX 300 → return

Invalidation (write-through):
  On any product create/update/deactivate/delete:
    SCAN + DEL product_plp:* (via Lua script for atomicity)
  On any category create/update/deactivate:
    SCAN + DEL product_plp:*

Trade-off: full cache flush on any write; acceptable at MVP scale (≤500 users);
           at scale, switch to tag-based invalidation.
```

**Resilience**: If Redis is unavailable → skip cache entirely, fall through to DB (fail-open).

---

## 2. Read/Write DB Routing Pattern

**Application**: All DB queries in Product Service

```
Writes (create/update/delete product, category, image, review):
  → SQLAlchemy async engine pointing to RDS PRIMARY endpoint

Reads (list_products, get_product_detail, list_reviews):
  → SQLAlchemy async engine pointing to RDS READ REPLICA endpoint

Implementation: Two separate async engines in database.py:
  write_engine = create_async_engine(PRIMARY_DSN, ...)
  read_engine  = create_async_engine(REPLICA_DSN, ...)
  
FastAPI Depends: get_write_db() / get_read_db() injected per router
```

---

## 3. tsvector FTS Maintenance Pattern

**Application**: Product full-text search

```
DB trigger (created in migration) fires AFTER INSERT OR UPDATE on products:
  NEW.search_vector := to_tsvector('english',
    coalesce(NEW.name, '') || ' ' ||
    coalesce(NEW.description, '') || ' ' ||
    coalesce(NEW.fabric_description, '')
  )

Category names added at query time via subquery weight boost:
  ts_rank(search_vector, query) + ts_rank(category_names_tsvector, query)

GIN index on search_vector ensures fast lookup.
```

---

## 4. Internal Service Client Pattern

**Application**: Calling Order Service for verified-purchase check

```
OrderServiceClient:
  - Async HTTP call via httpx with timeout 2s
  - 1 retry on connection error (tenacity)
  - On timeout/5xx: return is_reachable=False → treat as unverified (fail-open)
  - Uses internal network URL (not public API Gateway)
  - Shared-secret header for authentication

Pattern: Fail-open on dependency unavailability
  → review submission succeeds with is_verified_purchase=False if Order Service is down
  → order service being down must not block customers from writing reviews
```

---

## 5. Security Headers + Input Sanitisation Pattern

- `bleach.clean(description, tags=[], strip=True)` applied before storing product description/body
- `SecurityHeadersMiddleware` identical to Unit 1 applied to all responses
- S3 presigned URL scope: `PutObject` only on `products/{product_id}/*` prefix via IAM condition
