# Code Generation Plan — Unit 4: Order Microservice
# sabhyakriti-order-service

## Unit Context
| Repository | `sabhyakriti-order-service` | Port 8004 |
| Requirements | FR-CART-06–10, FR-ORD-01–09, FR-ACC-02–05, FR-ADM-07, FR-ADM-09 |
| Depends on | Unit 1 JWT, Unit 2 Product Service (stock), Unit 3 Cart Service (read/clear), Unit 5 Payment Service (refund), Unit 6 Notification Service |

## Steps
- [x] Step 1: Project setup (pyproject.toml, requirements incl. weasyprint, Dockerfile, docker-compose, CI/CD)
- [x] Step 2: Domain entities (Order, OrderItem, Address, ReturnRequest, ReturnItem, AddressSnapshot VO)
- [x] Step 3: Domain value objects (OrderStatus, ReturnStatus, PaymentMethod enums)
- [x] Step 4: Domain services (OrderDomainService: can_cancel, can_return, is_return_window_open, calculate_refund_amount, validate_status_transition)
- [x] Step 5: Repository interfaces
- [x] Step 6: Application DTOs (OrderDTO, OrderSummaryDTO, PagedOrderListDTO, ReturnRequestDTO, AddressDTO, InvoiceData)
- [x] Step 7: Application services:
  - OrderApplicationService (Flows 1–10)
  - AddressApplicationService (Flow 11)
- [x] Step 8: Service clients (CartServiceClient, ProductServiceClient, PaymentServiceClient, NotificationServiceClient)
- [x] Step 9: Infrastructure (SQLAlchemy models, repositories, dual engine, database.py)
- [x] Step 10: Invoice PDF generator (weasyprint HTML template → PDF bytes)
- [x] Step 11: Alembic migration (order schema + all tables + sequence + indexes)
- [x] Step 12: Presentation (middleware, routers, dependencies, main.py)
- [x] Step 13: Tests (domain PBT for refund calc, lifecycle tests, IDOR tests)
- [x] Step 14: Documentation
