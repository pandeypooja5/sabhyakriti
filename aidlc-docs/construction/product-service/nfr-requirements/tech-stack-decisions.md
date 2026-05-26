# Tech Stack Decisions — Unit 2: Product Microservice

## Runtime & Framework
| Component | Choice | Rationale |
|---|---|---|
| Language | Python 3.11 | Consistent with Unit 1 |
| Framework | FastAPI 0.111 | Async, Pydantic v2 |
| ASGI server | Uvicorn 0.29 | 4 workers for heavier load |

## Data Layer
| Component | Choice | Notes |
|---|---|---|
| ORM | SQLAlchemy 2.0 async | Async queries; `product` schema |
| Migrations | Alembic | tsvector trigger in migration |
| Read routing | `asyncpg` with two DSNs | Primary for writes, read replica for reads |
| FTS | PostgreSQL `tsvector` + GIN index | `plainto_tsquery` for safe query parsing |
| Cache | Redis DB 1 (shared ElastiCache) | PLP result cache, cache invalidation |

## Additional Libraries
| Library | Purpose |
|---|---|
| `python-slugify` | URL-safe slug generation |
| `bleach` | HTML sanitisation for product descriptions |
| `httpx` | Async HTTP for Order Service client |
| `tenacity` | Retry on Order Service calls |
| `boto3` | S3 presigned URLs, Secrets Manager |
| `structlog` | JSON logging |
| `hypothesis` | PBT for pricing and filter logic |
| `fakeredis` | Redis mock for tests |
| `pytest-asyncio`, `pytest-cov` | Testing |
