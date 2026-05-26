# Code Generation Plan — Unit 3: Cart & Wishlist Microservice
# sabhyakriti-cart-service

## Unit Context
| Field | Value |
|---|---|
| Repository | `sabhyakriti-cart-service` |
| Port | 8003 |
| Requirements | FR-CART-01–10, FR-ACC-06, FR-ADM-10 |
| Depends on | Unit 1 JWT, Unit 2 Product Service (live prices) |

## Steps (all marked complete after generation)
- [x] Step 1: Project setup (pyproject.toml, requirements, Dockerfile, docker-compose, CI/CD)
- [x] Step 2: Domain entities (Cart, CartItem, Wishlist, WishlistItem, Coupon, CartTotals VO)
- [x] Step 3: Domain services (PricingDomainService: totals calc, coupon apply logic)
- [x] Step 4: Repository interfaces
- [x] Step 5: Application DTOs (CartDTO, CartItemDTO, CartTotalsDTO, WishlistDTO, CouponDTO, etc.)
- [x] Step 6: Application services (CartApplicationService: flows 1–11, CouponApplicationService: flow 12)
- [x] Step 7: Product Service client (batch price fetch, fail-partial on timeout)
- [x] Step 8: Infrastructure (SQLAlchemy models, repositories, database.py)
- [x] Step 9: Alembic migration (cart schema + all tables + indexes)
- [x] Step 10: Presentation (middleware, routers, dependencies, main.py)
- [x] Step 11: Tests (domain PBT for totals/coupon, application tests, infrastructure tests)
- [x] Step 12: Documentation (code-summary.md, README.md)
