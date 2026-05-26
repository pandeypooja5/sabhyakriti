# Infrastructure Design — Unit 6: Notification Microservice

## AWS Mapping
| Component | Service | Config |
|---|---|---|
| Compute | EC2 t3.small (2 vCPU, 2GB) | Internal-only; Docker; port 8006 |
| Network | **No public ALB** — accessed only within VPC via internal DNS | VPC internal routing only |
| DB | RDS PostgreSQL `notification` schema | `notification_logs` table only |
| Email | AWS SES | `no-reply@sabhyakriti.com`; DKIM + SPF configured |
| SMS primary | Twilio | Sender number from Secrets Manager |
| SMS fallback | AWS SNS | SNS Transactional SMS (India DLT registered) |
| Logs | CloudWatch `/sabhyakriti/notification-service` | 90 days |
| Container | ECR `sabhyakriti/notification-service` | |

## Database Schema (notification)

```sql
CREATE SCHEMA IF NOT EXISTS notification;

CREATE TABLE notification.notification_logs (
    log_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notification_type VARCHAR(50) NOT NULL,
    channel           VARCHAR(10) NOT NULL,
    recipient         VARCHAR(255) NOT NULL,
    status            VARCHAR(10) NOT NULL DEFAULT 'SENT',
    provider          VARCHAR(20),
    error_message     TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notif_type ON notification.notification_logs(notification_type);
CREATE INDEX idx_notif_status ON notification.notification_logs(status);
CREATE INDEX idx_notif_created ON notification.notification_logs(created_at DESC);
```
