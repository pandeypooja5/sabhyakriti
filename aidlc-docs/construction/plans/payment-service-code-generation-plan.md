# Code Generation Plan — Unit 5: Payment Microservice
# sabhyakriti-payment-service

## Unit Context
| Repository | `sabhyakriti-payment-service` | Port 8005 |
| Requirements | FR-PAY-01 to FR-PAY-07 |
| Depends on | Unit 1 JWT, Unit 4 Order Service (confirm/cancel), Unit 6 Notification Service |

## Steps
- [x] 1: Project setup (pyproject.toml, requirements incl. razorpay + apscheduler, Dockerfile, docker-compose)
- [x] 2: Domain entities (Payment, WebhookEvent, PaymentStatus/PaymentMethod value objects)
- [x] 3: Domain services (RazorpaySignatureService: HMAC verify + webhook verify)
- [x] 4: Repository interfaces (IPaymentRepository, IWebhookEventRepository)
- [x] 5: Application DTOs (RazorpayOrderDTO, PaymentDTO, VerifyPaymentRequest, RefundDTO, PaymentReceiptDTO, WebhookPayload)
- [x] 6: Application services (PaymentApplicationService: all 7 flows)
- [x] 7: Service clients (OrderServiceClient, NotificationServiceClient)
- [x] 8: Razorpay adapter (razorpay SDK wrapper: create_order, create_refund)
- [x] 9: APScheduler background job (auto-cancel stale CREATED payments every 5min)
- [x] 10: Infrastructure (SQLAlchemy models, repositories, database.py, Alembic migration)
- [x] 11: Presentation (middleware, routers, dependencies, main.py)
- [x] 12: Tests (PBT HMAC, webhook idempotency, signature tamper, retry/auto-cancel)
- [x] 13: Documentation
