# Code Summary — Unit 8: AWS Infrastructure

~20 files generated under `sabhyakriti-infra/` (AWS CDK Python).

## Architecture: 5 Layered Stacks

| Stack | Key Resources |
|---|---|
| `SabhyakritiNetwork` | VPC (10.0.0.0/16), 2 AZs, 1 NAT gateway, 1 ALB SG + 7 service SGs + RDS SG + Redis SG, SSM VPC endpoints |
| `SabhyakritiDatabase` | RDS PostgreSQL 15 db.t3.small Multi-AZ + read replica, ElastiCache Redis cache.t3.micro, DB credentials in Secrets Manager |
| `SabhyakritiStorage` | S3 `sabhyakriti-product-images` (private, encrypted, CORS for presigned PUT), CloudFront (HTTPS-only, S3 OAC), SES domain identity, SNS SMS fallback topic |
| `SabhyakritiCompute` | 7 EC2 Auto Scaling Groups (1 per service), 1 shared ALB (HTTPS + HTTP→HTTPS redirect), path-based listener rules, ACM wildcard certificate, per-service least-privilege IAM roles |
| `SabhyakritiMonitoring` | 7 CloudWatch log groups (90-day retention), SNS alert topic, ALB 5xx alarm, per-service CPU alarms, auth login-failure alarm, unified CloudWatch dashboard |

## Security Compliance
- SECURITY-01: RDS + S3 encrypted at rest; all traffic TLS
- SECURITY-02: ALB access logging to S3
- SECURITY-06: Least-privilege IAM roles per service (no wildcards)
- SECURITY-07: Private subnets for all EC2/RDS/Redis; only ALB in public subnet
- SECURITY-09: S3 public access blocked; no default pages
- SECURITY-14: Log groups 90-day retention; alarms on security events

## Deployment Order
`Network` → `Database` → `Storage` → `Compute` → `Monitoring`

## Helper Scripts
- `scripts/deploy.sh` — deploys all 5 stacks in order
- `scripts/run_migrations.sh` — runs Alembic migrations for all 6 DB services

## Tests
- `tests/test_network_stack.py` — VPC CIDR, NAT count, SG count, HTTPS inbound, SSM endpoints
- `tests/test_storage_stack.py` — S3 public access blocked, encryption, CloudFront HTTPS-only
