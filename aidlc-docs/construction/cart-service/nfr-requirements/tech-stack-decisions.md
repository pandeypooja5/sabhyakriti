# Tech Stack Decisions — Unit 3: Cart & Wishlist Microservice

| Component | Choice | Notes |
|---|---|---|
| Language | Python 3.11 | Consistent |
| Framework | FastAPI 0.111 | |
| DB | PostgreSQL 15 (single engine — no replica needed; cart writes dominate) | `cart` schema |
| ORM | SQLAlchemy 2.0 async | |
| External client | httpx async | Product Service calls |
| Retry | tenacity | Product Service timeout handling |
| Validation | pydantic v2 | |
| Logging | structlog | |
| Testing | pytest + pytest-asyncio + hypothesis + fakeredis (not needed) + pytest-mock | |
