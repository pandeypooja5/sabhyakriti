# NFR Requirements — Unit 3: Cart & Wishlist Microservice

## Performance
| ID | Requirement | Target |
|---|---|---|
| NFR-CART-PERF-01 | Get cart + totals p95 (Product Service available) | < 400ms |
| NFR-CART-PERF-02 | Add/update/remove cart item p95 | < 300ms |
| NFR-CART-PERF-03 | Apply coupon p95 | < 200ms |
| NFR-CART-PERF-04 | Wishlist get p95 | < 350ms |

## Scalability
| EC2 | t3.medium (2 vCPU, 4GB) — lighter than Product Service |
| DB pool | pool_size=2, max_overflow=5 |
| No caching | Cart prices always fetched live from Product Service |

## Availability
- 99.9% uptime
- Product Service timeout → return stale prices with `price_stale=True` flag (fail-partial)
- Redis not used by Cart Service (no caching layer needed)

## Security
- All 15 SECURITY rules enforced
- Internal endpoints (`/internal/v1/*`) protected by shared-secret header only — not exposed via public ALB
- JWT validation on all customer endpoints
- Coupon codes sanitised before DB query (parameterised only)

## Testing
- 80% line coverage
- PBT (Hypothesis): cart totals formula (GST calculation, coupon discount boundaries), coupon validation edge cases
