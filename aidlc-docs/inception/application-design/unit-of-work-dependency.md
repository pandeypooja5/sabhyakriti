# Unit of Work — Dependency Matrix
# Sabhyakriti — Saree eCommerce Website

---

## 1. Dependency Matrix

A **→** B means Unit A calls Unit B at runtime (synchronous HTTP dependency).

| Unit | Depends On (Runtime) | Blocks (Must complete before) |
|---|---|---|
| **U1 Auth** | Redis, AWS SES, Google OAuth, Facebook OAuth, Twilio | U2, U3, U4, U5, U6, U7, U9 |
| **U2 Product** | U1 (JWT validation), AWS S3, CloudFront | U3, U4, U7, U9 |
| **U3 Cart** | U1 (JWT), U2 (product prices + availability) | U4, U7, U9 |
| **U4 Order** | U1 (JWT), U2 (stock reserve/release), U3 (read+clear cart), U6 (notify) | U5, U7, U9 |
| **U5 Payment** | U1 (JWT), U4 (update order status), U6 (notify), Razorpay API | U7, U9 |
| **U6 Notification** | U1 (user contact info), AWS SES, Twilio, AWS SNS | U9 (frontend relies on notifications firing) |
| **U7 Admin** | U1 (JWT + admin auth), U2, U3, U4, U5 (aggregation) | U9 (admin panel pages) |
| **U8 Infrastructure** | No runtime deps — provision environment for all units | All units must be deployed |
| **U9 Frontend** | U1–U7 APIs (via API Gateway), Razorpay JS SDK | None (final unit) |

---

## 2. Build Dependency Diagram

```
U1 Auth
  |
  +-----> U2 Product
  |           |
  |           +-----> U3 Cart
  |           |           |
  |           |           +-----> U4 Order
  |           |                       |
  |           |                       +-----> U5 Payment
  |           |                       |
  |           +-----------------------------> U7 Admin (aggregates all)
  |
  +-----> U6 Notification <---- U4, U5 (trigger notifications)
  |
  +-----> U8 Infrastructure (deploy all services)
              |
              +-----> U9 Frontend (all APIs stable)
```

---

## 3. Inter-Service Communication Details

| Caller | Called Service | Method | Endpoint | Purpose |
|---|---|---|---|---|
| U3 Cart | U2 Product | HTTP GET | `/api/v1/products/{id}` | Fetch current price + stock for cart pricing |
| U4 Order | U3 Cart | HTTP GET | `/internal/v1/cart/{user_id}` | Read cart contents at checkout |
| U4 Order | U3 Cart | HTTP DELETE | `/internal/v1/cart/{user_id}` | Clear cart after order created |
| U4 Order | U2 Product | HTTP PATCH | `/internal/v1/products/{id}/stock` | Reserve/release stock |
| U4 Order | U6 Notification | HTTP POST | `/internal/v1/notifications/order` | Trigger order status notifications |
| U5 Payment | U4 Order | HTTP PATCH | `/internal/v1/orders/{id}/status` | Update order status after payment |
| U5 Payment | U6 Notification | HTTP POST | `/internal/v1/notifications/payment` | Trigger payment/refund notifications |
| U6 Notification | U1 Auth | HTTP GET | `/internal/v1/users/{id}/contact` | Resolve email + phone for notifications |
| U7 Admin | U1–U5 | Various | Various internal endpoints | Aggregate data for admin views |

**Internal endpoints** (prefixed `/internal/v1/`) are not exposed via the public API Gateway — routed only within the private VPC subnet.

---

## 4. Shared Infrastructure Dependencies

| Resource | Used By | Purpose |
|---|---|---|
| **PostgreSQL RDS** | U1, U2, U3, U4, U5, U6 | Each service owns its schema: `auth`, `product`, `cart`, `order`, `payment`, `notification` |
| **Redis ElastiCache** | U1, U3 | U1: refresh tokens + OTP store; U3: coupon validation cache |
| **AWS S3** | U2, U8 | Product images (U2 generates presigned URLs; U8 creates the bucket) |
| **AWS CloudFront** | U2, U9 | CDN for product images (U2 builds URLs; U9 renders them) |
| **AWS SES** | U6 | Transactional email sending |
| **AWS SNS** | U6 | SMS fallback |
| **AWS CloudWatch** | U1–U7 | Structured log ingestion per service |
| **API Gateway (ALB)** | U1–U7 | All public traffic routes through ALB; path-based routing to each service |

---

## 5. Development Prerequisite Chain

To start development on a unit, the following must be complete:

| Unit | Prerequisites Before Starting Development |
|---|---|
| U1 Auth | Nothing — first unit |
| U2 Product | U1 JWT contract (public key, token format) agreed |
| U3 Cart | U1 JWT; U2 Product API contract (product detail endpoint) agreed |
| U4 Order | U1 JWT; U2 stock endpoint; U3 cart read/clear internal endpoints agreed |
| U5 Payment | U4 order status update internal endpoint agreed |
| U6 Notification | U1 user contact info endpoint agreed |
| U7 Admin | U1–U5 internal endpoints stable |
| U8 Infra | U1–U7 Dockerfiles + port assignments + env var requirements complete |
| U9 Frontend | U1–U7 public API contracts fully stable; U8 deployed to staging |

---

## 6. Risk Matrix

| Risk | Affected Units | Mitigation |
|---|---|---|
| Inter-service latency | U3, U4, U7 | Set HTTP timeouts; use read replicas for read-heavy Product calls |
| Circular dependency | None detected | Admin (U7) is aggregation-only; no circular loops |
| Razorpay webhook reliability | U5 | Idempotent webhook handler; log all webhook events; manual retry via admin |
| Stock race condition | U2, U4 | Use DB-level row locking (`SELECT FOR UPDATE`) in stock reservation transaction |
| Notification failures | U4, U5, U6 | Fire-and-forget; failures logged to CloudWatch; do not block order/payment flow |
| Solo dev complexity with microservices | All | Use Docker Compose for local development to run all services together |
