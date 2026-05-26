#!/usr/bin/env bash
# Run Alembic migrations for all backend services.
# Must be run after the database stack is deployed and RDS is accessible.
# Usage: run from a machine with network access to RDS (e.g., bastion or CI runner in VPC).
set -euo pipefail

DB_HOST="${1:?Usage: run_migrations.sh <rds-endpoint>}"

SERVICES=(
    "sabhyakriti-auth-service"
    "sabhyakriti-product-service"
    "sabhyakriti-cart-service"
    "sabhyakriti-order-service"
    "sabhyakriti-payment-service"
    "sabhyakriti-notification-service"
)

for svc in "${SERVICES[@]}"; do
    echo "==> Running migrations for ${svc}..."
    pushd "../${svc}" > /dev/null
    DATABASE_URL="postgresql+asyncpg://sabhyakriti_admin:${DB_PASSWORD}@${DB_HOST}:5432/sabhyakriti" \
        alembic upgrade head
    popd > /dev/null
    echo "    Done."
done

echo "All migrations complete."
