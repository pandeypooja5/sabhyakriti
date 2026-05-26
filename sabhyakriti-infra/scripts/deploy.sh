#!/usr/bin/env bash
# Deploy all Sabhyakriti CDK stacks in dependency order.
set -euo pipefail

export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
export CDK_DEFAULT_REGION="ap-south-1"

echo "Deploying to account ${CDK_DEFAULT_ACCOUNT} in ${CDK_DEFAULT_REGION}"

# Bootstrap CDK (only needed once per account/region)
# cdk bootstrap

echo "==> Deploying Network stack..."
cdk deploy SabhyakritiNetwork --require-approval never

echo "==> Deploying Database stack..."
cdk deploy SabhyakritiDatabase --require-approval never

echo "==> Deploying Storage stack..."
cdk deploy SabhyakritiStorage --require-approval never

echo "==> Deploying Compute stack..."
cdk deploy SabhyakritiCompute --require-approval never

echo "==> Deploying Monitoring stack..."
cdk deploy SabhyakritiMonitoring --require-approval never

echo ""
echo "All stacks deployed successfully."
echo "Next steps:"
echo "  1. Verify SES domain identity in the AWS console"
echo "  2. Update Route 53 DNS: api.sabhyakriti.com -> ALB DNS"
echo "  3. Update Route 53 DNS: cdn.sabhyakriti.com -> CloudFront domain"
echo "  4. Run: scripts/run_migrations.sh to apply all Alembic migrations"
echo "  5. Push Docker images to ECR for each service"
