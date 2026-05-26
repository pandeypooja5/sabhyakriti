#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# start-local.sh — Start all Sabhyakriti services locally
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

WORKSPACE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$WORKSPACE"

echo "Starting Sabhyakriti local stack..."
echo ""

# ── 1. Build and start all backend services + DB ──────────────────────────────
echo "==> Building Docker images (first run takes 3-5 minutes)..."
docker compose -f docker-compose.all.yml build --parallel

echo ""
echo "==> Starting PostgreSQL + Redis..."
docker compose -f docker-compose.all.yml up -d postgres redis

echo "Waiting for database to be ready..."
until docker compose -f docker-compose.all.yml exec -T postgres pg_isready -U postgres -q; do
  sleep 2
done
echo "  PostgreSQL: ready"

until docker compose -f docker-compose.all.yml exec -T redis redis-cli ping | grep -q PONG; do
  sleep 1
done
echo "  Redis: ready"

# ── 2. Run database migrations for all services ───────────────────────────────
echo ""
echo "==> Running database migrations..."

SERVICES_WITH_DB=(auth product cart order payment notification)
for svc in "${SERVICES_WITH_DB[@]}"; do
  echo "  Migrating ${svc}-service..."
  docker compose -f docker-compose.all.yml run --rm \
    -e DATABASE_URL="postgresql+asyncpg://postgres:postgres@postgres:5432/sabhyakriti" \
    ${svc}-service \
    alembic upgrade head 2>&1 | tail -3
done
echo "  All migrations complete."

# ── 3. Start all backend services ────────────────────────────────────────────
echo ""
echo "==> Starting all backend services..."
docker compose -f docker-compose.all.yml up -d \
  auth-service product-service cart-service \
  order-service payment-service notification-service admin-service

# ── 4. Wait for all services healthy ─────────────────────────────────────────
echo ""
echo "==> Waiting for services to be healthy..."
SERVICES=(auth-service product-service cart-service order-service payment-service admin-service)
for svc in "${SERVICES[@]}"; do
  echo -n "  $svc "
  for i in {1..30}; do
    STATUS=$(docker compose -f docker-compose.all.yml ps --format json "$svc" 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(d[0].get('Health',''))" 2>/dev/null || echo "")
    if [ "$STATUS" = "healthy" ]; then
      echo "✓"
      break
    fi
    echo -n "."
    sleep 3
  done
done

# ── 5. Print URLs ─────────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════"
echo "  All backend services running!"
echo ""
echo "  Service endpoints:"
echo "    Auth:         http://localhost:8001/docs"
echo "    Product:      http://localhost:8002/docs"
echo "    Cart:         http://localhost:8003/docs"
echo "    Order:        http://localhost:8004/docs"
echo "    Payment:      http://localhost:8005/docs"
echo "    Notification: http://localhost:8006/health (internal only)"
echo "    Admin BFF:    http://localhost:8007/api/docs"
echo ""
echo "  Next step — start the frontend:"
echo "    cd sabhyakriti-frontend && npm run dev"
echo "    Open http://localhost:5173"
echo ""
echo "  To seed sample data:"
echo "    python3 scripts/seed-data.py"
echo ""
echo "  To stop all services:"
echo "    docker compose -f docker-compose.all.yml down"
echo "════════════════════════════════════════════════════════"
