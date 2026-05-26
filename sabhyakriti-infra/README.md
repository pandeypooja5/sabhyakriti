# sabhyakriti-infra

AWS CDK (Python) infrastructure for the Sabhyakriti Saree eCommerce Platform.

## Stacks

| Stack | Description |
|-------|-------------|
| `SabhyakritiNetwork` | VPC, subnets (2 AZs), NAT gateway, security groups, SSM VPC endpoints |
| `SabhyakritiDatabase` | RDS PostgreSQL 15 Multi-AZ + read replica + ElastiCache Redis |
| `SabhyakritiStorage` | S3 (product images) + CloudFront CDN + SES + SNS |
| `SabhyakritiCompute` | EC2 Auto Scaling (7 services) + ALB + path-based routing |
| `SabhyakritiMonitoring` | CloudWatch log groups + alarms + dashboard |

## Prerequisites

```bash
pip install -r requirements.txt
npm install -g aws-cdk   # CDK CLI
aws configure            # AWS credentials for ap-south-1
```

## Bootstrap (once per account/region)

```bash
export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
cdk bootstrap aws://$CDK_DEFAULT_ACCOUNT/ap-south-1
```

## Deploy

```bash
export ADMIN_ALERT_EMAIL=your-email@example.com
bash scripts/deploy.sh
```

## Run DB Migrations (after first deploy)

```bash
export DB_PASSWORD=<from-secrets-manager>
bash scripts/run_migrations.sh <rds-endpoint>
```

## Tests

```bash
pytest tests/
```

## Service Ports

| Service | Port | EC2 Type |
|---------|------|----------|
| auth-service | 8001 | t3.medium |
| product-service | 8002 | t3.large |
| cart-service | 8003 | t3.medium |
| order-service | 8004 | t3.medium |
| payment-service | 8005 | t3.medium |
| notification-service | 8006 | t3.small (internal only) |
| admin-service | 8007 | t3.small |
