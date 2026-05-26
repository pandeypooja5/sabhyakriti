# Build Instructions — Sabhyakriti Platform

## System Requirements
- Python 3.11+
- Node.js 20 LTS+
- Docker Desktop 4.x+
- Docker Compose v2+
- AWS CLI v2 + CDK CLI 2.143+
- Git

---

## 1. Backend Services (Units 1–7: Python/FastAPI)

Run these steps for **each** of the 7 backend repositories:

```
sabhyakriti-auth-service
sabhyakriti-product-service
sabhyakriti-cart-service
sabhyakriti-order-service
sabhyakriti-payment-service
sabhyakriti-notification-service
sabhyakriti-admin-service
```

### 1.1 Install Dependencies

```bash
cd sabhyakriti-{service-name}
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

### 1.2 Configure Environment

```bash
cp .env.example .env
# Fill in required values for local development:
#   DATABASE_URL = postgresql+asyncpg://postgres:postgres@localhost:5432/sabhyakriti_{service}
#   REDIS_URL    = redis://localhost:6379/0   (auth + product services only)
#   ENVIRONMENT  = development
# Leave Razorpay/OAuth/AWS keys as dummy values for unit tests
```

### 1.3 Start Local Dependencies (Docker Compose)

```bash
docker-compose -f docker-compose.dev.yml up -d
```

Starts PostgreSQL 15 + Redis 7 (where applicable).

### 1.4 Run Alembic Migrations (DB services only — not admin-service)

```bash
alembic upgrade head
```

### 1.5 Verify Service Starts

```bash
uvicorn main:app --port {SERVICE_PORT} --reload
# auth=8001, product=8002, cart=8003, order=8004, payment=8005, notification=8006, admin=8007
```

Expected output:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:{PORT}
```

Health check: `curl http://localhost:{PORT}/health` → `{"status": "ok"}`

---

## 2. AWS Infrastructure (Unit 8: CDK)

```bash
cd sabhyakriti-infra
pip install -r requirements.txt

# Bootstrap (first time only)
export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
cdk bootstrap aws://$CDK_DEFAULT_ACCOUNT/ap-south-1

# Synthesise (validate templates without deploying)
cdk synth

# Deploy (requires AWS credentials with AdministratorAccess)
export ADMIN_ALERT_EMAIL=admin@sabhyakriti.com
bash scripts/deploy.sh
```

Expected: 5 stacks deploy successfully — `SabhyakritiNetwork`, `SabhyakritiDatabase`, `SabhyakritiStorage`, `SabhyakritiCompute`, `SabhyakritiMonitoring`

---

## 3. Frontend (Unit 9: React/Vite)

```bash
cd sabhyakriti-frontend
npm install

cp .env.example .env
# Fill in:
#   VITE_API_BASE_URL=http://localhost:8001   (or local reverse proxy)
#   VITE_RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxx  (Razorpay test key)

npm run build           # production build → dist/
npm run preview         # preview production build locally
```

Expected build output:
```
✓ 2500 modules transformed.
dist/index.html                   1.20 kB
dist/assets/index-[hash].css    145.00 kB
dist/assets/index-[hash].js     890.00 kB
```

Type check separately:
```bash
npm run type-check    # npx tsc --noEmit
npm run lint          # ESLint
```

---

## 4. All Services Together (docker-compose.all.yml)

Create a root-level compose file to run everything locally:

```bash
# From C:\AI-Projects\sabhyakriti\
docker compose -f docker-compose.all.yml up --build
```

Services available:
- Auth:    http://localhost:8001/docs
- Product: http://localhost:8002/docs
- Cart:    http://localhost:8003/docs
- Order:   http://localhost:8004/docs
- Payment: http://localhost:8005/docs
- Notif:   http://localhost:8006 (internal only)
- Admin:   http://localhost:8007/api/docs
- Frontend: http://localhost:5173

---

## Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| `asyncpg.PostgresConnectionError` | DB not running | `docker-compose up -d db` |
| `alembic: FAILED` | Schema not created | Ensure `DATABASE_URL` correct; run `alembic upgrade head` |
| `ModuleNotFoundError` | venv not activated | `source .venv/bin/activate` |
| `Port already in use` | Conflict | Change port in `.env` or stop conflicting process |
| CDK `Error: Need to perform AWS calls` | No AWS credentials | `aws configure` or set env vars |
| `npm: ENOENT package.json` | Wrong directory | `cd sabhyakriti-frontend` first |
