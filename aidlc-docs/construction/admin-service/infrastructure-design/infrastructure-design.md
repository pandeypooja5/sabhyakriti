# Infrastructure Design — Unit 7: Admin Microservice

## AWS Mapping
| Component | Service | Config |
|---|---|---|
| Compute | EC2 t3.small | Private subnet; Docker; port 8007 |
| Load balancer | ALB (shared) | `/api/v1/admin/*` → port 8007 |
| **NO database** | — | Admin Service has no own schema |
| Logs | CloudWatch `/sabhyakriti/admin-service` | 90 days |
| Container | ECR `sabhyakriti/admin-service` | |

## Service Clients Required
| Client | Target Service | Base URL Env Var |
|---|---|---|
| `OrderServiceClient` | Order Service | `ORDER_SERVICE_URL` |
| `ProductServiceClient` | Product Service | `PRODUCT_SERVICE_URL` |
| `AuthServiceClient` | Auth Service | `AUTH_SERVICE_URL` |
| `CartServiceClient` | Cart Service | `CART_SERVICE_URL` |

All clients use internal VPC routing + `X-Internal-Secret` header for internal endpoints;
admin JWT passed through for public admin endpoints.
