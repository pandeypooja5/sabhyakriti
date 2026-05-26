#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# setup-local.sh — One-time local development environment setup
# Run once before first `docker compose up`
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

WORKSPACE="$(cd "$(dirname "$0")/.." && pwd)"
echo "Setting up Sabhyakriti local development environment..."
echo "Workspace: $WORKSPACE"

# ── 1. Check prerequisites ────────────────────────────────────────────────────
echo ""
echo "==> Checking prerequisites..."

command -v docker >/dev/null 2>&1 || { echo "ERROR: Docker not found. Install Docker Desktop."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "ERROR: Python 3 not found."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "ERROR: Node.js not found. Install Node.js 20 LTS."; exit 1; }
command -v openssl >/dev/null 2>&1 || { echo "ERROR: openssl not found."; exit 1; }

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
NODE_VERSION=$(node --version)
echo "  Python: $PYTHON_VERSION"
echo "  Node:   $NODE_VERSION"
echo "  Docker: $(docker --version | awk '{print $3}' | tr -d ',')"
echo "  Prerequisites: OK"

# ── 2. Generate RSA key pair for JWT (RS256) ──────────────────────────────────
echo ""
echo "==> Generating RSA-2048 key pair for JWT signing..."
KEY_DIR="$WORKSPACE/.jwt-keys"
mkdir -p "$KEY_DIR"

if [ ! -f "$KEY_DIR/private.pem" ]; then
  openssl genrsa -out "$KEY_DIR/private.pem" 2048
  openssl rsa -in "$KEY_DIR/private.pem" -pubout -out "$KEY_DIR/public.pem"
  echo "  Generated: $KEY_DIR/private.pem"
  echo "  Generated: $KEY_DIR/public.pem"
else
  echo "  JWT keys already exist — skipping."
fi

# Write private key to auth service .env
PRIVATE_KEY=$(cat "$KEY_DIR/private.pem" | base64 | tr -d '\n')
echo "JWT_PRIVATE_KEY_B64=$PRIVATE_KEY" > "$WORKSPACE/sabhyakriti-auth-service/.env.jwt"
echo "  Auth service JWT key configured."

# ── 3. Copy .env files for each service ──────────────────────────────────────
echo ""
echo "==> Configuring service .env files..."

SERVICES=(auth product cart order payment notification admin)
PORTS=(8001 8002 8003 8004 8005 8006 8007)

for i in "${!SERVICES[@]}"; do
  svc="${SERVICES[$i]}"
  port="${PORTS[$i]}"
  env_file="$WORKSPACE/sabhyakriti-${svc}-service/.env"
  if [ ! -f "$env_file" ]; then
    cp "$WORKSPACE/sabhyakriti-${svc}-service/.env.example" "$env_file"
    echo "  Created .env for ${svc}-service"
  else
    echo "  .env for ${svc}-service already exists — skipping."
  fi
done

# ── 4. Frontend .env ──────────────────────────────────────────────────────────
echo ""
echo "==> Configuring frontend .env..."
FRONTEND_ENV="$WORKSPACE/sabhyakriti-frontend/.env"
if [ ! -f "$FRONTEND_ENV" ]; then
  cat > "$FRONTEND_ENV" << 'EOF'
VITE_API_BASE_URL=http://localhost:8001
VITE_RAZORPAY_KEY_ID=rzp_test_XXXXXXXXXXXX
EOF
  echo "  Created frontend .env"
  echo "  ACTION REQUIRED: Update VITE_RAZORPAY_KEY_ID in sabhyakriti-frontend/.env"
else
  echo "  Frontend .env already exists — skipping."
fi

# ── 5. Install frontend dependencies ─────────────────────────────────────────
echo ""
echo "==> Installing frontend dependencies..."
cd "$WORKSPACE/sabhyakriti-frontend"
npm install --silent
echo "  npm install: done"

# ── 6. Summary ────────────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════"
echo "  Setup complete!"
echo ""
echo "  Next steps:"
echo "  1. Edit .env.local — add your Razorpay TEST keys"
echo "  2. Run: bash scripts/start-local.sh"
echo "  3. In a second terminal: cd sabhyakriti-frontend && npm run dev"
echo "  4. Open http://localhost:5173"
echo ""
echo "  To seed sample data (after services start):"
echo "  python3 scripts/seed-data.py"
echo "════════════════════════════════════════════════════════"
