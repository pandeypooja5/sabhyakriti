# Code Summary — Unit 3: Cart & Wishlist Microservice

58 files generated under `sabhyakriti-cart-service/`.

## Key Implementation Highlights
- `CartTotals` uses `Decimal` arithmetic with `ROUND_HALF_UP` — no float rounding errors
- GST (5%) calculated on net amount (subtotal − discount), shown as separate line item
- Free shipping always (₹0)
- FLAT coupon capped at subtotal; PERCENT coupon uncapped
- `get_or_create` cart uses `SELECT FOR UPDATE` to prevent race conditions
- `add_item` enforces 20-product limit and 10-quantity limit at application layer
- Product Service timeout → returns empty price map → `price_stale=True` flag in response
- Internal endpoints (`/internal/v1/*`) protected by shared-secret header
- Internal clear-cart is idempotent (safe to call multiple times)
- Wishlist add is idempotent (INSERT ON CONFLICT DO NOTHING)
- All 12 business flows from business-logic-model.md implemented

## Tests
- Hypothesis PBT: 8 total properties including total invariant, GST=5% of net (not gross), shipping=0, coupon boundary conditions
- 9 parametrised coupon validation cases
- 10 application service unit tests (mocked repos)
- 9 repository integration tests
