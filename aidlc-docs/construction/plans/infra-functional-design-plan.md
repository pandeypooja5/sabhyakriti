# Functional Design Plan — Unit 8: AWS Infrastructure
# sabhyakriti-infra

---

## Execution Checklist

- [ ] Step 1: Answer questions (user fills [Answer]: tags below)
- [ ] Step 2: Analyze answers
- [ ] Step 3: Generate CDK infrastructure code
- [ ] Step 4: Present for approval

---

## Context Summary

Unit 8 uses AWS CDK (Python) to codify all infrastructure for all 9 services.
Most decisions are already locked from each service's infrastructure-design.md:
- AWS Region: ap-south-1 (Mumbai — closest to India)
- 7 backend services on EC2 (t3.small to t3.large), Docker, SSM deployments
- 1 shared ALB with path-based routing
- RDS PostgreSQL 15 Multi-AZ (shared instance with per-service schemas)
- ElastiCache Redis (shared cache.t3.micro, DB indices per service)
- S3 + CloudFront for product images
- AWS SES, SNS for email/SMS
- CloudWatch for logs + alarms

Only 2 decisions genuinely remain open:

---

## Question 1
Should the CDK be structured as separate stacks per concern or one monolithic stack?

A) Layered stacks — NetworkStack, DatabaseStack, ComputeStack, StorageStack, MonitoringStack (recommended: easier to deploy/update individually)
B) Single stack — all resources in one CDK stack (simpler, but slower to update and harder to maintain)
C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 2
Should we provision a separate staging/QA environment, or production-only for now?

A) Production only — one set of CDK stacks for prod; developers use docker-compose locally
B) Production + Staging — two environments, staging uses smaller/cheaper instance types (t3.micro)
C) Other (please describe after [Answer]: tag below)

[Answer]: B
