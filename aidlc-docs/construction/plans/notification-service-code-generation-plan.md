# Code Generation Plan — Unit 6: Notification Microservice
# sabhyakriti-notification-service

## Unit Context
| Repository | `sabhyakriti-notification-service` | Port 8006 (internal only) |
| Requirements | FR-ORD-07, FR-ORD-08, FR-AUTH-05, FR-AUTH-07 + all notification triggers |
| Callers | Units 1, 4, 5 (Auth, Order, Payment Services) |

## Steps
- [x] 1: Project setup
- [x] 2: Domain entities (NotificationLog, enums)
- [x] 3: Repository interface + SQLAlchemy implementation
- [x] 4: Jinja2 email templates (10 HTML files)
- [x] 5: Application service (NotificationApplicationService: send_email, send_sms with fallback)
- [x] 6: AWS SES adapter (send_email with retry)
- [x] 7: Twilio SMS adapter (send_sms with 2 retries → fallback to SNS)
- [x] 8: AWS SNS adapter (fallback SMS)
- [x] 9: Pydantic request DTOs for all 13 notification types
- [x] 10: FastAPI routers (13 internal endpoints + health)
- [x] 11: Infrastructure (DB, Alembic migration)
- [x] 12: main.py + middleware
- [x] 13: Tests (template rendering, send_email/sms with mock adapters, fallback path)
- [x] 14: Documentation
