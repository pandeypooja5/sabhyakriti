# Infrastructure Design — Unit 2: Product Microservice

---

## AWS Service Mapping

| Logical Component | AWS Service | Config |
|---|---|---|
| Compute | EC2 t3.large | Private subnet; Docker; port 8002 |
| Load balancer | ALB (shared, Unit 8) | Path-based routing → target group port 8002 |
| DB writes | RDS PostgreSQL 15 primary | `product` schema; `db.t3.small` |
| DB reads | RDS read replica | `db.t3.small`; used for all PLP/PDP queries |
| PLP cache | ElastiCache Redis DB 1 | Shared cache.t3.micro (DB 0 = Auth, DB 1 = Product) |
| Image storage | S3 bucket `sabhyakriti-product-images` | Block all public access; server-side encryption (SSE-S3) |
| Image CDN | CloudFront distribution | Origin: S3; OAC (Origin Access Control) only — no direct S3 access; custom domain `cdn.sabhyakriti.com` |
| Secrets | AWS Secrets Manager | DB passwords, S3 bucket name, CloudFront domain, Order Service URL |
| Logs | CloudWatch `/sabhyakriti/product-service` | 90-day retention |
| Metrics | CloudWatch `Sabhyakriti/Product` | PLPCacheHit, PLPCacheMiss, ProductCreated, ReviewCreated |
| Container registry | ECR `sabhyakriti/product-service` | Image scanning on push |
| CI/CD | GitHub Actions | Same pipeline pattern as Unit 1 |

---

## Network

```
ALB (public, 443) → sg-product-ec2 (private, 8002)
                  → sg-rds (5432, from sg-product-ec2)
                  → sg-redis (6379, from sg-product-ec2)
S3 ← CloudFront OAC only (no public S3 access)
/internal/v1/* → ALB internal listener (port 8080, accessible only within VPC)
```

---

## Database Schema (product)

```sql
CREATE SCHEMA IF NOT EXISTS product;

CREATE TABLE product.products (
    product_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(200) NOT NULL,
    slug                VARCHAR(220) NOT NULL UNIQUE,
    sku                 VARCHAR(100) UNIQUE,
    description         TEXT,
    price               NUMERIC(10,2) NOT NULL CHECK (price > 0),
    discount_percentage NUMERIC(5,2) NOT NULL DEFAULT 0
                        CHECK (discount_percentage >= 0 AND discount_percentage <= 100),
    stock_qty           INTEGER NOT NULL DEFAULT 0 CHECK (stock_qty >= 0),
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    average_rating      NUMERIC(3,2) NOT NULL DEFAULT 0.00,
    review_count        INTEGER NOT NULL DEFAULT 0,
    search_vector       TSVECTOR,
    blouse_included     BOOLEAN NOT NULL DEFAULT FALSE,
    fabric_description  VARCHAR(200),
    care_instructions   TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE product.categories (
    category_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          VARCHAR(100) NOT NULL,
    type          VARCHAR(20) NOT NULL CHECK (type IN ('FABRIC','OCCASION','REGION')),
    slug          VARCHAR(120) NOT NULL UNIQUE,
    display_order SMALLINT NOT NULL DEFAULT 0,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE product.product_categories (
    product_id  UUID NOT NULL REFERENCES product.products(product_id) ON DELETE CASCADE,
    category_id UUID NOT NULL REFERENCES product.categories(category_id) ON DELETE CASCADE,
    PRIMARY KEY (product_id, category_id)
);

CREATE TABLE product.product_images (
    image_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id      UUID NOT NULL REFERENCES product.products(product_id) ON DELETE CASCADE,
    s3_key          VARCHAR(500) NOT NULL UNIQUE,
    cloudfront_url  VARCHAR(600) NOT NULL,
    is_primary      BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order      SMALLINT NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE product.reviews (
    review_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id          UUID NOT NULL REFERENCES product.products(product_id) ON DELETE CASCADE,
    user_id             UUID NOT NULL,
    rating              SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    title               VARCHAR(150) NOT NULL,
    body                TEXT,
    is_verified_purchase BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (product_id, user_id)
);

-- Indexes
CREATE INDEX idx_products_slug ON product.products(slug);
CREATE INDEX idx_products_active ON product.products(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_products_search ON product.products USING GIN(search_vector);
CREATE INDEX idx_products_rating ON product.products(average_rating DESC);
CREATE INDEX idx_products_created ON product.products(created_at DESC);
CREATE INDEX idx_products_stock ON product.products(stock_qty);
CREATE INDEX idx_categories_type_active ON product.categories(type, is_active);
CREATE INDEX idx_pc_product ON product.product_categories(product_id);
CREATE INDEX idx_pc_category ON product.product_categories(category_id);
CREATE INDEX idx_images_product ON product.product_images(product_id, sort_order);
CREATE UNIQUE INDEX idx_images_primary ON product.product_images(product_id)
    WHERE is_primary = TRUE;
CREATE INDEX idx_reviews_product ON product.reviews(product_id, created_at DESC);

-- FTS trigger
CREATE OR REPLACE FUNCTION product.update_search_vector() RETURNS trigger AS $$
BEGIN
  NEW.search_vector := to_tsvector('english',
    coalesce(NEW.name,'') || ' ' ||
    coalesce(NEW.description,'') || ' ' ||
    coalesce(NEW.fabric_description,'')
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_products_search
BEFORE INSERT OR UPDATE ON product.products
FOR EACH ROW EXECUTE FUNCTION product.update_search_vector();
```

---

## Redis Key Design (DB 1)

| Key Pattern | TTL | Purpose |
|---|---|---|
| `product_plp:{sha256_of_query_params}` | 300s (5 min) | Cached PLP JSON response |
| `product_detail:{product_id}` | 600s (10 min) | Cached PDP JSON (optional future optimisation) |

Cache invalidation: `SCAN + DEL product_plp:*` on any product/category write.

---

## IAM Role (EC2 Product Service)

Key permissions (least-privilege, SECURITY-06):
- `s3:PutObject` on `arn:aws:s3:::sabhyakriti-product-images/products/*` (presigned upload)
- `s3:DeleteObject` on same prefix (image delete)
- `secretsmanager:GetSecretValue` on `sabhyakriti/product/*`
- `logs:PutLogEvents` on `/sabhyakriti/product-service`
- `cloudwatch:PutMetricData` scoped to `Sabhyakriti/Product` namespace
- `ecr:*` for image pull
